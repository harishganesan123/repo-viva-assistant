import json
import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import ai_engine
from app.database import get_db
from app.models import (
    AnalysisResult,
    Repository,
    RepositoryFile,
    Report,
    User,
)
from app.repo_parser import (
    fetch_file_content,
    parse_repository,
)
from app.schemas import (
    AnalysisOut,
    AnalyzeRequest,
    FileExplainRequest,
    FunctionExplainRequest,
    RepositoryOut,
)
from app.security import get_current_user

router = APIRouter(
    prefix="/api/repos",
    tags=["repositories"],
)


@router.post("/analyze", response_model=RepositoryOut)
def analyze_repository(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = Repository(
        owner_id=current_user.id,
        repo_url=payload.repo_url,
        status="scanning",
    )

    db.add(repo)
    db.commit()
    db.refresh(repo)

    try:
        structure = parse_repository(payload.repo_url)

    except ValueError as exc:
        repo.status = "failed"
        repo.error_message = str(exc)

        db.commit()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    repo.repo_name = structure.repo_name
    repo.default_branch = structure.default_branch

    for f in structure.files:
        db.add(
            RepositoryFile(
                repository_id=repo.id,
                path=f.path,
                language=f.language,
                size_bytes=f.size_bytes,
                is_important=1 if f.important else 0,
            )
        )

    try:
        context = ai_engine.build_project_context(structure)

        print("STEP 1 - Project Summary")
        summary = ai_engine.generate_project_summary(context)

        print("STEP 2 - Folder Explanations")
        folders = ai_engine.generate_folder_explanations(
            structure,
            context,
        )

        print("STEP 3 - Viva Questions")
        viva = ai_engine.generate_viva_questions(context)

        print("STEP 4 - Interview Questions")
        interview = ai_engine.generate_interview_questions(context)

        print("STEP 5 - Insights")
        insights = ai_engine.generate_insights(
            structure,
            context,
        )

        print("STEP 6 - Learning Notes")
        learning = ai_engine.generate_learning_notes(structure)

        print("ALL AI TASKS COMPLETED")

    except Exception as exc:
        print("========== FULL ERROR ==========")
        traceback.print_exc()
        print("================================")

        repo.status = "failed"
        repo.error_message = f"Analysis failed: {exc}"

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=repo.error_message,
        )

    tech_stack = {
        "languages": structure.languages,
        "frameworks": sorted(structure.frameworks),
        "has_database": structure.has_database,
        "has_auth": structure.has_auth,
    }

    db.add(
        AnalysisResult(
            repository_id=repo.id,
            tech_stack_json=json.dumps(tech_stack),
            project_summary_json=json.dumps(summary),
            folder_explanations_json=json.dumps(folders),
            viva_questions_json=json.dumps(viva),
            interview_questions_json=json.dumps(interview),
            insights_json=json.dumps(insights),
            learning_notes_json=json.dumps(learning),
        )
    )

    html_report = ai_engine.render_report_html(
        repo.repo_name,
        summary,
        folders,
        viva,
        interview,
        insights,
        learning,
    )

    db.add(
        Report(
            repository_id=repo.id,
            html_content=html_report,
        )
    )

    repo.status = "analyzed"

    db.commit()
    db.refresh(repo)

    return repo
@router.get("", response_model=list[RepositoryOut])
    
def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Repository)
        .filter(Repository.owner_id == current_user.id)
        .order_by(Repository.created_at.desc())
        .all()
    )


@router.get("/{repo_id}", response_model=RepositoryOut)
def get_repository(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = _get_owned_repo(
        db,
        repo_id,
        current_user,
    )

    return repo


@router.get("/{repo_id}/analysis", response_model=AnalysisOut)
def get_analysis(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = _get_owned_repo(
        db,
        repo_id,
        current_user,
    )

    if not repo.analysis:
        raise HTTPException(
            status_code=404,
            detail="This repository hasn't been analyzed yet.",
        )

    analysis = repo.analysis

    return AnalysisOut(
        tech_stack=json.loads(
            analysis.tech_stack_json or "null"
        ),
        project_summary=json.loads(
            analysis.project_summary_json or "null"
        ),
        folder_explanations=json.loads(
            analysis.folder_explanations_json or "null"
        ),
        viva_questions=json.loads(
            analysis.viva_questions_json or "null"
        ),
        interview_questions=json.loads(
            analysis.interview_questions_json or "null"
        ),
        insights=json.loads(
            analysis.insights_json or "null"
        ),
        learning_notes=json.loads(
            analysis.learning_notes_json or "null"
        ),
    )
@router.post("/{repo_id}/files/explain")
def explain_file(
    repo_id: int,
    payload: FileExplainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = _get_owned_repo(
        db,
        repo_id,
        current_user,
    )

    try:
        content = fetch_file_content(
            repo.repo_url,
            payload.path,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    explanation = ai_engine.generate_file_explanation(
        payload.path,
        content,
    )

    return {
        "path": payload.path,
        "explanation": explanation,
    }


@router.post("/{repo_id}/functions/explain")
def explain_function(
    repo_id: int,
    payload: FunctionExplainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = _get_owned_repo(
        db,
        repo_id,
        current_user,
    )

    try:
        content = fetch_file_content(
            repo.repo_url,
            payload.path,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    explanation = ai_engine.generate_function_explanation(
        payload.path,
        payload.function_name,
        content,
    )

    return {
        "path": payload.path,
        "function": payload.function_name,
        "explanation": explanation,
    }
def _get_owned_repo(
    db: Session,
    repo_id: int,
    current_user: User,
) -> Repository:
    repo = (
        db.query(Repository)
        .filter(
            Repository.id == repo_id,
            Repository.owner_id == current_user.id,
        )
        .first()
    )

    if repo is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found.",
        )

    return repo 
    
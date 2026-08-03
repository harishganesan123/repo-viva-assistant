from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnalysisResult, Repository, Report, User
from app.schemas import DashboardStats
from app.security import get_current_user

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/repos/{repo_id}/report", response_class=HTMLResponse)
def get_report(repo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo or repo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found.")
    if not repo.report:
        raise HTTPException(status_code=404, detail="Report not generated yet.")
    return HTMLResponse(content=repo.report.html_content)


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    repos = (
        db.query(Repository)
        .filter(Repository.owner_id == current_user.id)
        .order_by(Repository.created_at.desc())
        .all()
    )
    analyzed = [r for r in repos if r.status == "analyzed"]
    reports_count = db.query(Report).join(Repository).filter(Repository.owner_id == current_user.id).count()

    questions_count = 0
    for r in analyzed:
        if r.analysis:
            import json
            viva = json.loads(r.analysis.viva_questions_json or "[]")
            interview = json.loads(r.analysis.interview_questions_json or "[]")
            questions_count += len(viva) + len(interview)

    return DashboardStats(
        repositories_analyzed=len(analyzed),
        reports_generated=reports_count,
        questions_generated=questions_count,
        recent=repos[:5],
    )

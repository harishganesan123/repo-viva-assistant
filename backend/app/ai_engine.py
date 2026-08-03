"""
AI Explanation Engine

Wraps every AI-backed module (project summary, folder/file/function
explanations, viva questions, interview questions, learning notes,
insights) behind small, focused prompts that request JSON back so the
frontend can render structured cards instead of raw prose.

Provider note: the master spec calls for Google Gemini. This prototype
uses the Anthropic API instead (see README) — swap `_call_ai` for a
Gemini client if you want to switch providers; every other module is
provider-agnostic.
"""

import json
import re
from typing import Any

from google import genai

from app.config import settings
from app.repo_parser import RepoStructure

_client = None


def _get_client():
    global _client

    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set — add it to backend/.env"
            )

        _client = genai.Client(
            api_key=settings.gemini_api_key
        )

    return _client


def _call_ai(system: str, user: str, max_tokens: int = 2000) -> str:
    print("MODEL =", repr(settings.gemini_model))
    client = _get_client()

    prompt = f"""
{system}

{user}
"""

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        print("Gemini call successful")
        print("Response type:", type(response))
        print("Has text:", hasattr(response, "text"))

        try:
            print("========== GEMINI RESPONSE ==========")
            print(response.text)
            print("=====================================")
        except Exception as e:
            print("ERROR READING response.text")
            print(type(e))
            print(e)
            raise

        return response.text

    except Exception as e:
        print("========== GEMINI ERROR ==========")
        print(type(e))
        print(e)
        print("==================================")
        raise


def _parse_json(raw: str) -> Any:
    """AI output is asked to be pure JSON, but strip code fences defensively."""
    cleaned = re.sub(
        r"^```(json)?|```$",
        "",
        raw.strip(),
        flags=re.MULTILINE,
    ).strip()

    return json.loads(cleaned)


JSON_SYSTEM_PREFIX = (
    "You are a senior software engineer explaining a student's own project to them "
    "ahead of a viva/interview. Be clear, concrete, and grounded only in the project "
    "context given — never invent files or behavior that isn't there. "
    "Respond with ONLY valid JSON matching the requested shape. "
    "No prose, no markdown fences."
)
def build_project_context(structure: RepoStructure, max_files_content: int = 8) -> str:
    """Flatten the parsed repo into a compact context block for prompts."""
    lines = [
        f"Repository: {structure.repo_name}",
        f"Top-level folders: {', '.join(structure.top_level_dirs) or 'none'}",
        f"Languages: {', '.join(f'{lang} ({n} files)' for lang, n in structure.languages.items()) or 'unknown'}",
        f"Detected frameworks/tools: {', '.join(sorted(structure.frameworks)) or 'none detected'}",
        f"Config files: {', '.join(structure.config_files) or 'none'}",
        f"Appears to use a database: {structure.has_database}",
        f"Appears to have authentication: {structure.has_auth}",
        f"Total files scanned: {len(structure.files)}",
        "",
        "Contents of key files:",
    ]

    shown = 0
    for f in structure.files:
        if f.content and shown < max_files_content:
            lines.append(f"\n--- {f.path} ---\n{f.content[:4000]}")
            shown += 1

    return "\n".join(lines)


def generate_project_summary(context: str) -> dict:
    schema = (
        '{"project_name": str, "objective": str, "overview": str, '
        '"workflow": str, "architecture": str, "tech_stack": [str], '
        '"advantages": [str], "limitations": [str], "possible_improvements": [str]}'
    )

    raw = _call_ai(
        JSON_SYSTEM_PREFIX,
        f"Project context:\n{context}\n\nReturn JSON with exactly this shape:\n{schema}",
    )

    return _parse_json(raw)


def generate_folder_explanations(structure: RepoStructure, context: str) -> list[dict]:
    if not structure.top_level_dirs:
        return []

    schema = (
        '[{"folder": str, "purpose": str, '
        '"responsibilities": [str], "important_files": [str]}]'
    )

    raw = _call_ai(
        JSON_SYSTEM_PREFIX,
        f"Project context:\n{context}\n\n"
        f"Top-level folders to explain: {', '.join(structure.top_level_dirs)}\n\n"
        f"Return a JSON array with this shape:\n{schema}",
    )

    return _parse_json(raw)


def generate_file_explanation(path: str, content: str) -> dict:
    schema = (
        '{"purpose": str, "role": str, "workflow": str, '
        '"dependencies": [str], "functions": [str], '
        '"interacts_with": [str]}'
    )

    raw = _call_ai(
        JSON_SYSTEM_PREFIX,
        f"File path: {path}\n\n"
        f"File content:\n{content[:6000]}\n\n"
        f"Return JSON with exactly this shape:\n{schema}",
    )

    return _parse_json(raw)


def generate_function_explanation(
    path: str,
    function_name: str,
    file_content: str,
) -> dict:
    schema = (
        '{"purpose": str, "parameters": [str], '
        '"return_value": str, "algorithm": str, '
        '"time_complexity": str, "example_usage": str, '
        '"why_it_exists": str}'
    )

    raw = _call_ai(
        JSON_SYSTEM_PREFIX,
        f"File path: {path}\n"
        f"Function to explain: {function_name}\n\n"
        f"Full file content for context:\n{file_content[:6000]}\n\n"
        f"Return JSON with exactly this shape:\n{schema}",
    )

    return _parse_json(raw)


def generate_viva_questions(context: str) -> list[dict]:
    schema = (
        '[{"category": str, '
        '"difficulty": "easy"|"medium"|"hard", '
        '"question": str, '
        '"answer": str, '
        '"explanation": str, '
        '"follow_ups": [str]}]'
    )

    raw = _call_ai(
        JSON_SYSTEM_PREFIX,
        f"Project context:\n{context}\n\n"
        "Generate 15 viva questions covering project overview, "
        "architecture, backend, frontend, database, authentication, "
        "API design, and deployment — grounded in what's actually in "
        f"this repo. Return a JSON array with this shape:\n{schema}",
        max_tokens=4000,
    )

    print("========== VIVA RAW RESPONSE ==========")
    print(raw)
    print("=======================================")

    return _parse_json(raw)


def generate_interview_questions(context: str) -> list[dict]:
    schema = (
        '[{"topic": str, '
        '"question": str, '
        '"expected_answer": str}]'
    )

    raw = _call_ai(
        JSON_SYSTEM_PREFIX,
        f"Project context:\n{context}\n\n"
        "Generate 12 placement-style interview questions: "
        "some general (language, REST APIs, Git, SQL, system design) "
        "and some specific to this repo's stack. "
        f"Return a JSON array with this shape:\n{schema}",
        max_tokens=3000,
    )

    return _parse_json(raw)


def generate_learning_notes(structure: RepoStructure) -> list[dict]:
    if not structure.frameworks:
        return []

    schema = (
        '[{"technology": str, '
        '"explanation": str, '
        '"beginner_guide": str, '
        '"intermediate_concepts": str, '
        '"advanced_concepts": str, '
        '"real_world_applications": str, '
        '"interview_tips": str}]'
    )

    raw = _call_ai(
        JSON_SYSTEM_PREFIX,
        f"Technologies detected in this project: "
        f"{', '.join(sorted(structure.frameworks))}\n\n"
        f"Return a JSON array with this shape:\n{schema}",
        max_tokens=3000,
    )

    return _parse_json(raw)


def generate_insights(structure: RepoStructure, context: str) -> dict:
    schema = (
        '{"code_quality": str, '
        '"project_complexity": str, '
        '"documentation_quality": str, '
        '"folder_organization": str, '
        '"coding_practices": str, '
        '"security_observations": str, '
        '"scalability_notes": str, '
        '"improvement_suggestions": [str]}'
    )

    raw = _call_ai(
        JSON_SYSTEM_PREFIX + " Keep tone constructive, not harsh.",
        f"Project context:\n{context}\n\n"
        f"Return JSON with exactly this shape:\n{schema}",
    )

    return _parse_json(raw)
def render_report_html(
    repo_name: str,
    summary: dict,
    folders: list[dict],
    viva: list[dict],
    interview: list[dict],
    insights: dict,
    learning: list[dict],
) -> str:

    def li(items: list[str]) -> str:
        return "".join(f"<li>{i}</li>" for i in items)

    folder_html = "".join(
        f"<h3>{f['folder']}</h3>"
        f"<p>{f['purpose']}</p>"
        f"<ul>{li(f.get('important_files', []))}</ul>"
        for f in folders
    )

    viva_html = "".join(
        f"<div class='q'>"
        f"<b>[{q['difficulty']}] {q['question']}</b>"
        f"<p>{q['answer']}</p>"
        f"</div>"
        for q in viva
    )

    interview_html = "".join(
        f"<div class='q'>"
        f"<b>{q['question']}</b>"
        f"<p>{q['expected_answer']}</p>"
        f"</div>"
        for q in interview
    )

    learning_html = "".join(
        f"<h3>{t['technology']}</h3>"
        f"<p>{t['explanation']}</p>"
        for t in learning
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{repo_name} — AI report</title>

<style>
body {{
    font-family: -apple-system, Arial, sans-serif;
    max-width: 820px;
    margin: 40px auto;
    color: #1a1a1a;
}}

h1 {{
    font-size: 24px;
}}

h2 {{
    font-size: 19px;
    border-bottom: 1px solid #ddd;
    padding-bottom: 6px;
    margin-top: 32px;
}}

h3 {{
    font-size: 15px;
    margin-bottom: 4px;
}}

.q {{
    margin-bottom: 14px;
}}

ul {{
    padding-left: 20px;
}}
</style>

</head>

<body>

<h1>{repo_name} — AI Project Report</h1>

<h2>Project Summary</h2>

<p><b>Objective:</b> {summary.get("objective", "")}</p>

<p>{summary.get("overview", "")}</p>

<p><b>Architecture:</b> {summary.get("architecture", "")}</p>

<p><b>Tech Stack:</b> {", ".join(summary.get("tech_stack", []))}</p>

<h2>Folder Explanations</h2>

{folder_html or "<p>No folders detected.</p>"}

<h2>Viva Questions</h2>

{viva_html}

<h2>Interview Questions</h2>

{interview_html}

<h2>Learning Notes</h2>

{learning_html or "<p>No specific technologies detected.</p>"}

<h2>Insights</h2>

<p><b>Code Quality:</b> {insights.get("code_quality", "")}</p>

<p><b>Improvement Suggestions:</b></p>

<ul>
{li(insights.get("improvement_suggestions", []))}
</ul>

</body>
</html>
"""
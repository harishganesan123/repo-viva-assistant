# AI-powered GitHub repository analyzer & viva assistant

A working prototype: paste a GitHub repo URL, and it clones the repo, reads
the structure and key files, and generates a full viva/interview prep
report — project summary, architecture, folder-by-folder explanations,
on-demand file/function explanations, viva questions, interview questions,
learning notes, and code insights.

## What's real vs. simplified vs. swapped, compared to the original spec

- **AI provider**: the spec asks for Google Gemini. This sandbox can only
  reach `api.anthropic.com`, so the analysis engine calls the **Anthropic
  API** instead (`app/ai_engine.py`). Every prompt/module is provider-agnostic —
  swap `_call_ai()` for a Gemini client if you want to switch back.
- **Database**: SQLite instead of Postgres, to keep the demo to one file
  with zero setup. Same SQLAlchemy models — change `DATABASE_URL` in `.env`
  to point at Postgres and nothing else needs to change.
- **Everything else** (auth, repo cloning/scanning, all 12 modules, the
  dashboard, the HTML report) is implemented and was tested end-to-end
  against a real GitHub repo during the build — not stubbed.
- **Not built**: PDF export (marked optional in the spec) and a background
  job queue — analysis runs synchronously in the request, which is fine
  for a demo repo but will feel slow on a large one.

## Project layout

```
backend/    FastAPI + SQLAlchemy + JWT auth + repo parser + AI engine
frontend/   React (Vite) + Tailwind + React Router + Axios
```

## Running it

### 1. Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate    # or your usual venv tool
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`:
- `JWT_SECRET` — generate one with `openssl rand -hex 32`
- `ANTHROPIC_API_KEY` — get one at https://console.anthropic.com

Then run it:

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).
Tables are created automatically on first run.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. Sign up, then paste a public GitHub
repo URL on the "Analyze repository" page.

## How the pieces fit together (module → code)

| Spec module | Where it lives |
|---|---|
| Authentication | `backend/app/security.py`, `backend/app/routers/auth.py` |
| Repository Parser | `backend/app/repo_parser.py` |
| Repository Analyzer / Folder / File / Function explanation | `backend/app/ai_engine.py` |
| Viva & Interview Question Generators | `ai_engine.generate_viva_questions` / `generate_interview_questions` |
| Learning Assistant | `ai_engine.generate_learning_notes` |
| Repository Insights | `ai_engine.generate_insights` |
| Report Generator | `ai_engine.render_report_html`, served at `GET /api/repos/{id}/report` |
| Dashboard | `frontend/src/pages/Dashboard.jsx`, `GET /api/dashboard/stats` |

## Known limitations to be upfront about

- Analysis is synchronous — a large repo (hundreds of files) will make the
  "Run analysis" request take a while. A production version would push
  this to a background worker and poll for status.
- The AI engine sends a summarized context (top-level structure + a
  handful of "important" files) rather than the entire repo, to keep
  requests small and fast — this is standard practice for repo-analysis
  tools but means very large or deeply nested projects get a lighter-touch
  analysis.
- No rate limiting / retry logic around the AI calls yet.

# AI-powered GitHub Repository Analyzer & Viva Assistant

A working prototype: paste a GitHub repository URL, and it clones the repository, reads its structure and key files, and generates a full viva/interview preparation report — project summary, architecture, folder explanations, on-demand file/function explanations, viva questions, interview questions, learning notes, code insights, and an HTML report.

## Current implementation

- **AI provider:** Google Gemini via the `google-genai` SDK.
- **Database:** SQLite by default for local development; PostgreSQL is supported for production through the same `DATABASE_URL` setting.
- **Authentication:** JWT-based authentication.
- **Backend:** FastAPI + SQLAlchemy.
- **Frontend:** React + Vite + Tailwind CSS + React Router + Axios.
- **Repository analysis:** GitPython is used to clone and scan public GitHub repositories.
- **Report:** HTML report served by the backend.
- **Not built:** PDF export and a background job queue. Analysis currently runs synchronously, which is suitable for a demo but can be slow for large repositories.

## Project layout

```
backend/    FastAPI + SQLAlchemy + JWT auth + repository parser + Gemini AI engine
frontend/   React (Vite) + Tailwind + React Router + Axios
```

## Local development

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate    # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env       # Windows PowerShell: Copy-Item .env.example .env
```

Edit `backend/.env`:

- `JWT_SECRET` — generate a strong random value, for example with `openssl rand -hex 32`.
- `GEMINI_API_KEY` — your Google Gemini API key.
- `GEMINI_MODEL` — defaults to `gemini-2.5-flash`.
- `DATABASE_URL` — SQLite locally; use PostgreSQL in production.
- `FRONTEND_URL` — `http://localhost:5173` locally and your deployed frontend URL in production.

Run:

```bash
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. Interactive API documentation is available at `/docs`, and the health endpoint is `/api/health`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

The frontend API URL is controlled by:

```env
VITE_API_URL=http://localhost:8000
```

For production, set `VITE_API_URL` to the deployed FastAPI backend URL.

## Production deployment

A simple deployment is:

- **Frontend:** Vercel
- **Backend:** Render or another Python-compatible web-service host
- **Database:** PostgreSQL
- **AI:** Google Gemini

### Backend environment variables

Set these in the backend hosting provider:

```env
JWT_SECRET=<strong-random-secret>
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=<postgresql-connection-string>
CLONE_DIR=./tmp_repos
FRONTEND_URL=https://<your-frontend-domain>
```

Start the backend with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Frontend environment variable

Set:

```env
VITE_API_URL=https://<your-backend-domain>
```

The backend CORS configuration allows the local development frontend and the production URL supplied through `FRONTEND_URL`.

## How the pieces fit together

| Module | Where it lives |
|---|---|
| Authentication | `backend/app/security.py`, `backend/app/routers/auth.py` |
| Repository Parser | `backend/app/repo_parser.py` |
| Repository / folder / file / function analysis | `backend/app/ai_engine.py` |
| Viva questions | `generate_viva_questions` |
| Interview questions | `generate_interview_questions` |
| Learning Assistant | `generate_learning_notes` |
| Repository Insights | `generate_insights` |
| Report Generator | `render_report_html`, served at `GET /api/repos/{id}/report` |
| Dashboard | `frontend/src/pages/Dashboard.jsx`, `GET /api/dashboard/stats` |

## Known limitations

- Analysis is synchronous. Large repositories can make the analysis request take a while. A production-scale version could use a background worker and status polling.
- The AI engine sends a summarized repository context and a limited number of key file contents rather than the entire repository.
- There is currently no rate limiting or retry strategy around AI calls.
- Temporary cloned repositories are stored under `CLONE_DIR` and are not intended as permanent storage.

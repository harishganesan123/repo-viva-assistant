import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, repos, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-Powered GitHub Repository Analyzer & Viva Assistant")

allowed_origins = [
    "http://localhost:5173",
    os.getenv("FRONTEND_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in allowed_origins if origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(repos.router)
app.include_router(reports.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

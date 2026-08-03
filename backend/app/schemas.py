from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr


# ---- Auth ----

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Repositories ----

class AnalyzeRequest(BaseModel):
    repo_url: str


class RepositoryOut(BaseModel):
    id: int
    repo_url: str
    repo_name: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FileExplainRequest(BaseModel):
    path: str


class FunctionExplainRequest(BaseModel):
    path: str
    function_name: str


class DashboardStats(BaseModel):
    repositories_analyzed: int
    reports_generated: int
    questions_generated: int
    recent: list[RepositoryOut]


class AnalysisOut(BaseModel):
    tech_stack: Any = None
    project_summary: Any = None
    folder_explanations: Any = None
    viva_questions: Any = None
    interview_questions: Any = None
    insights: Any = None
    learning_notes: Any = None

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    repositories = relationship("Repository", back_populates="owner")


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repo_url = Column(String, nullable=False)
    repo_name = Column(String, nullable=True)
    default_branch = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending | scanning | analyzed | failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="repositories")
    files = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")
    analysis = relationship("AnalysisResult", back_populates="repository", uselist=False, cascade="all, delete-orphan")
    report = relationship("Report", back_populates="repository", uselist=False, cascade="all, delete-orphan")


class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    path = Column(String, nullable=False)
    language = Column(String, nullable=True)
    size_bytes = Column(Integer, default=0)
    is_important = Column(Integer, default=0)  # 0/1 flag — cheap boolean for sqlite

    repository = relationship("Repository", back_populates="files")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), unique=True, nullable=False)

    tech_stack_json = Column(Text, nullable=True)       # detected languages/frameworks
    project_summary_json = Column(Text, nullable=True)  # summary, objective, architecture, workflow
    folder_explanations_json = Column(Text, nullable=True)
    file_explanations_json = Column(Text, nullable=True)  # keyed by file path, filled lazily on click
    viva_questions_json = Column(Text, nullable=True)
    interview_questions_json = Column(Text, nullable=True)
    insights_json = Column(Text, nullable=True)
    learning_notes_json = Column(Text, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repository = relationship("Repository", back_populates="analysis")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), unique=True, nullable=False)
    html_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship("Repository", back_populates="report")

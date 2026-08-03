"""
Module 1 — Repository Parser

Clones a GitHub repo, walks the tree, skips noise directories/binaries,
and produces a lightweight structural summary plus a shortlist of
"important" files whose content is worth sending to the AI engine.
"""
import os
import re
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from git import Repo, GitCommandError

from app.config import settings

IGNORE_DIRS = {
    "node_modules", "venv", ".venv", ".git", "dist", "build",
    "__pycache__", ".next", ".turbo", "target", "bin", "obj",
    "coverage", ".pytest_cache", ".mypy_cache", "vendor", ".idea", ".vscode",
}

BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mov", ".exe", ".dll", ".so",
    ".class", ".jar", ".db", ".sqlite", ".sqlite3",
}

# Files whose content is almost always worth reading in full.
IMPORTANT_FILENAMES = {
    "readme.md", "package.json", "requirements.txt", "pyproject.toml",
    "main.py", "app.py", "manage.py", "settings.py", "urls.py",
    "index.js", "index.ts", "app.js", "app.ts", "server.js",
    "dockerfile", "docker-compose.yml", ".env.example",
    "pom.xml", "build.gradle", "go.mod", "cargo.toml",
}

LANGUAGE_BY_EXT = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (React)",
    ".ts": "TypeScript", ".tsx": "TypeScript (React)", ".java": "Java",
    ".go": "Go", ".rb": "Ruby", ".php": "PHP", ".rs": "Rust",
    ".c": "C", ".cpp": "C++", ".cs": "C#", ".html": "HTML", ".css": "CSS",
    ".sql": "SQL", ".sh": "Shell",
}

MAX_FILE_BYTES = 60_000       # skip reading anything larger than this
MAX_TOTAL_CONTEXT_BYTES = 250_000  # cap total bytes sent to the AI engine


@dataclass
class ParsedFile:
    path: str
    language: Optional[str]
    size_bytes: int
    important: bool
    content: Optional[str] = None  # populated only for important/small files


@dataclass
class RepoStructure:
    repo_name: str
    default_branch: Optional[str]
    files: list[ParsedFile] = field(default_factory=list)
    languages: dict = field(default_factory=dict)     # language -> file count
    frameworks: set = field(default_factory=set)
    config_files: list[str] = field(default_factory=list)
    has_database: bool = False
    has_auth: bool = False
    top_level_dirs: list[str] = field(default_factory=list)


def _clone_repo(repo_url: str, dest: Path) -> Repo:
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)
    try:
        repo = Repo.clone_from(repo_url, dest, depth=1)
    except GitCommandError as exc:
        raise ValueError(f"Could not clone repository: {exc}") from exc
    return repo


def _detect_frameworks(paths: list[str], contents: dict) -> set:
    frameworks = set()
    pkg = contents.get("package.json", "")
    req = contents.get("requirements.txt", "") + contents.get("pyproject.toml", "")

    checks = {
        "React": "\"react\"" in pkg,
        "Next.js": "\"next\"" in pkg,
        "Vue": "\"vue\"" in pkg,
        "Express": "\"express\"" in pkg,
        "FastAPI": "fastapi" in req.lower(),
        "Django": "django" in req.lower(),
        "Flask": "flask" in req.lower(),
        "TensorFlow": "tensorflow" in req.lower(),
        "PyTorch": "torch" in req.lower(),
        "Tailwind CSS": "\"tailwindcss\"" in pkg,
        "SQLAlchemy": "sqlalchemy" in req.lower(),
    }
    for name, present in checks.items():
        if present:
            frameworks.add(name)

    lower_paths = " ".join(paths).lower()
    if "dockerfile" in lower_paths:
        frameworks.add("Docker")
    if ".github/workflows" in lower_paths:
        frameworks.add("GitHub Actions")
    return frameworks


def parse_repository(repo_url: str) -> RepoStructure:
    """Clone + walk a repo, returning a structural summary and important-file contents."""
    repo_name = re.sub(r"\.git$", "", repo_url.rstrip("/").split("/")[-1]) or "repository"
    clone_dir = Path(settings.clone_dir).resolve() / f"{repo_name}_{os.getpid()}"

    repo = _clone_repo(repo_url, clone_dir)
    try:
        default_branch = repo.active_branch.name
    except TypeError:
        default_branch = None

    structure = RepoStructure(repo_name=repo_name, default_branch=default_branch)
    contents_by_filename: dict = {}
    total_context_bytes = 0

    for root, dirs, filenames in os.walk(clone_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".git")]
        rel_root = Path(root).relative_to(clone_dir)
        if rel_root == Path("."):
            structure.top_level_dirs = sorted(
                d for d in dirs if d not in IGNORE_DIRS
            )

        for filename in filenames:
            full_path = Path(root) / filename
            rel_path = str(full_path.relative_to(clone_dir))
            ext = full_path.suffix.lower()

            if ext in BINARY_EXTS:
                continue
            try:
                size_bytes = full_path.stat().st_size
            except OSError:
                continue

            language = LANGUAGE_BY_EXT.get(ext)
            is_important = filename.lower() in IMPORTANT_FILENAMES

            content = None
            if is_important and size_bytes <= MAX_FILE_BYTES and total_context_bytes < MAX_TOTAL_CONTEXT_BYTES:
                try:
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    total_context_bytes += len(content)
                    contents_by_filename[filename.lower()] = content
                except OSError:
                    content = None

            structure.files.append(ParsedFile(
                path=rel_path, language=language, size_bytes=size_bytes,
                important=is_important, content=content,
            ))
            if language:
                structure.languages[language] = structure.languages.get(language, 0) + 1

    all_paths = [f.path for f in structure.files]
    structure.frameworks = _detect_frameworks(all_paths, contents_by_filename)
    structure.config_files = [
        f.path for f in structure.files
        if Path(f.path).name.lower() in IMPORTANT_FILENAMES
    ]
    joined_paths = " ".join(all_paths).lower()
    structure.has_database = any(k in joined_paths for k in ("models.py", "schema.sql", "migrations", "prisma"))
    structure.has_auth = any(k in joined_paths for k in ("auth", "jwt", "login", "passport"))

    # Best-effort cleanup of the clone — don't fail the request over it.
    shutil.rmtree(clone_dir, ignore_errors=True)

    return structure


def fetch_file_content(repo_url: str, relative_path: str) -> str:
    """Re-clone (shallow) just to pull one file's content for on-demand explanation."""
    repo_name = re.sub(r"\.git$", "", repo_url.rstrip("/").split("/")[-1]) or "repository"
    clone_dir = Path(settings.clone_dir).resolve() / f"{repo_name}_lookup_{os.getpid()}"
    _clone_repo(repo_url, clone_dir)
    try:
        target = clone_dir / relative_path
        if not target.exists():
            raise ValueError(f"File not found in repository: {relative_path}")
        return target.read_text(encoding="utf-8", errors="ignore")
    finally:
        shutil.rmtree(clone_dir, ignore_errors=True)


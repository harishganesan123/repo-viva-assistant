from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = "dev_secret_change_me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"

    database_url: str = "sqlite:///./repo_analyzer.db"
    clone_dir: str = "./tmp_repos"

    class Config:
        env_file = ".env"


settings = Settings()

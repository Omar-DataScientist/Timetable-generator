"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    APP_NAME: str = "Timetable Generator"
    DATABASE_URL: str = "sqlite+aiosqlite:///./timetable.db"
    SOLVER_TIME_LIMIT_SECONDS: int = 120
    SOLVER_NUM_WORKERS: int = 8
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

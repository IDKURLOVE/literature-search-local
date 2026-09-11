from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_SQLITE = _BACKEND_DIR / "litscope.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Native default: local SQLite file. Override for Postgres via DATABASE_URL.
    database_url: str = f"sqlite+aiosqlite:///{_DEFAULT_SQLITE.as_posix()}"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    app_secret_key: str = "change-me-in-production"
    crossref_mailto: Optional[str] = None
    semantic_scholar_api_key: Optional[str] = None
    topic_refresh_crontab: str = "0 */6 * * *"
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"

    # Native deploy: in-process scheduler instead of Celery/Redis
    enable_scheduler: bool = True
    scheduler_interval_hours: int = 6
    # "auto" = try Celery, fall back in-process; "inline" = never Celery
    refresh_mode: str = "auto"


settings = Settings()

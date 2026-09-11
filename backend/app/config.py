from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://litscope:litscope@localhost:5432/litscope"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    app_secret_key: str = "change-me-in-production"
    crossref_mailto: Optional[str] = None
    semantic_scholar_api_key: Optional[str] = None
    topic_refresh_crontab: str = "0 */6 * * *"
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"


settings = Settings()

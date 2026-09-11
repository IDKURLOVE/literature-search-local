from celery import Celery
from celery.schedules import crontab

from app.config import settings


def parse_crontab(expr: str) -> crontab:
    """Parse standard 5-field cron: minute hour day_of_month month day_of_week."""
    parts = expr.split()
    if len(parts) != 5:
        parts = ["0", "*/6", "*", "*", "*"]
    minute, hour, day_of_month, month_of_year, day_of_week = parts
    return crontab(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
    )


celery_app = Celery(
    "litscope",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"],
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "refresh-all-topics": {
            "task": "app.tasks.refresh_all_topics",
            "schedule": parse_crontab(settings.topic_refresh_crontab),
        },
    },
)

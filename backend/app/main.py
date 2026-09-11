import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import export, papers, search, topics

logger = logging.getLogger("litscope")


async def _scheduler_loop() -> None:
    from app.tasks import refresh_all_topics_async

    interval = max(settings.scheduler_interval_hours, 1) * 3600
    await asyncio.sleep(5)
    while True:
        try:
            await refresh_all_topics_async()
        except Exception:
            logger.exception("Scheduled topic refresh failed")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    scheduler_task = None
    if settings.enable_scheduler and settings.refresh_mode != "celery-only":
        scheduler_task = asyncio.create_task(_scheduler_loop())

    yield

    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
    await engine.dispose()


app = FastAPI(
    title="LitScope Local",
    description="本地自动化文献查阅 Web 应用 — developed with Xiaomi MIMO (MiMo-X-Pro-Preview)",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(topics.router, prefix="/api/topics", tags=["topics"])
app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(export.router, prefix="/api/export", tags=["export"])


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "litscope-local",
        "database": "sqlite" if settings.database_url.startswith("sqlite") else "external",
        "scheduler": settings.enable_scheduler,
        "refresh_mode": settings.refresh_mode,
        "built_with": "Xiaomi MIMO — MiMo-X-Pro-Preview",
    }

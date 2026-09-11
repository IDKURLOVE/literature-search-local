import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

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
    description="本地自动化文献查�?Web 应用 �?developed with Xiaomi MIMO (MiMo-X-Pro-Preview)",
    version="1.1.5",
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


@app.get("/", include_in_schema=False)
async def root():
    return HTMLResponse(
        """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>LitScope Local · API</title>
  <style>
    body { font-family: Georgia, "Times New Roman", serif; background: #faf9f5; color: #141413;
           max-width: 40rem; margin: 12vh auto; padding: 0 1.5rem; line-height: 1.65; }
    a { color: #cc785c; }
    code { font-family: ui-monospace, Consolas, monospace; background: #f5f0e8;
           padding: 0.1em 0.35em; border-radius: 4px; }
    .muted { color: #6c6a64; font-size: 0.95rem; }
  </style>
</head>
<body>
  <h1>LitScope Local</h1>
  <p>这是 <strong>API 服务</strong>（默�?<code>:8000</code>），不是完整界面�?/p>
  <ul>
    <li>界面请打开�?a href="http://localhost:3000">http://localhost:3000</a></li>
    <li>健康检查：<a href="/api/health">/api/health</a></li>
    <li>Swagger�?a href="/docs">/docs</a></li>
  </ul>
  <p class="muted">�?3000 打不开，请在另一终端启动前端�?code>cd frontend &amp;&amp; npm run dev</code></p>
  <p class="muted">Developed with Xiaomi MIMO �?MiMo-X-Pro-Preview</p>
</body>
</html>
"""
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="/")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "litscope-local",
        "database": "sqlite" if settings.database_url.startswith("sqlite") else "external",
        "scheduler": settings.enable_scheduler,
        "refresh_mode": settings.refresh_mode,
        "built_with": "Xiaomi MIMO �?MiMo-X-Pro-Preview",
    }

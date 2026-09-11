import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.database import AsyncSessionLocal, Base, engine
from app.models import Paper, Topic, surname_lower
from app.schemas import PaperCreate, SearchRequest
from app.sources import normalize_title, search_all


async def _ensure_schema() -> None:
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def refresh_topic_async(topic_id: str) -> None:
    """In-process refresh (native deploy / fallback when Celery is unavailable)."""
    await _refresh_topic(topic_id)


async def refresh_all_topics_async() -> None:
    await _ensure_schema()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Topic.id))
        topic_ids = [row[0] for row in result.all()]
    for topic_id in topic_ids:
        await _refresh_topic(str(topic_id))


@celery_app.task(name="app.tasks.refresh_topic")
def refresh_topic(topic_id: str) -> None:
    asyncio.run(_refresh_topic(topic_id))


@celery_app.task(name="app.tasks.refresh_all_topics")
def refresh_all_topics() -> None:
    asyncio.run(refresh_all_topics_async())


def queue_refresh(topic_id: str) -> str:
    """Queue refresh via Celery when allowed; return mode used."""
    from app.config import settings

    if settings.refresh_mode == "inline":
        return "inline-required"
    try:
        refresh_topic.delay(str(topic_id))
        return "celery"
    except Exception:
        return "inline-required"


async def _refresh_topic(topic_id: str) -> None:
    await _ensure_schema()
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Topic).options(selectinload(Topic.papers)).where(Topic.id == UUID(topic_id))
        )
        topic = result.scalar_one_or_none()
        if not topic:
            return

        request = SearchRequest(
            query=topic.query,
            sources=topic.sources or ["crossref", "openalex"],
            filters=topic.filters or {},
            limit=50,
        )
        search_result = await search_all(request)
        papers_data = search_result["papers"]

        current_papers = list(topic.papers or [])
        existing_dois = {p.doi for p in current_papers if p.doi}

        for p_data in papers_data:
            p_create = PaperCreate(**{k: v for k, v in p_data.items() if k != "id"})
            paper = await _get_or_create_paper(db, p_create)
            if paper.doi and paper.doi in existing_dois:
                continue
            if paper not in current_papers:
                current_papers.append(paper)
                if paper.doi:
                    existing_dois.add(paper.doi)

        topic.papers = current_papers
        topic.last_results_count = len(current_papers)
        await db.commit()


async def _get_or_create_paper(db, p_data: PaperCreate) -> Paper:
    doi = p_data.doi
    if doi:
        result = await db.execute(select(Paper).where(Paper.doi == doi))
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    title_norm = normalize_title(p_data.title)
    first_author = surname_lower(p_data.authors[0].name) if p_data.authors else ""
    result = await db.execute(select(Paper).where(Paper.year == p_data.year))
    for existing in result.scalars().all():
        if existing.to_normalized_title() == title_norm and (existing.first_author or "") == first_author:
            return existing

    paper = Paper(**p_data.model_dump())
    db.add(paper)
    await db.flush()
    return paper

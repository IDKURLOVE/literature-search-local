from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Topic
from app.schemas import TopicCreate, TopicOut, TopicUpdate
from app.tasks import queue_refresh, refresh_topic_async

router = APIRouter()


def _schedule_refresh(topic_id: str, background: BackgroundTasks) -> str:
    mode = queue_refresh(topic_id)
    if mode == "celery":
        return "queued-celery"
    background.add_task(refresh_topic_async, topic_id)
    return "queued-inline"


@router.post("/", response_model=TopicOut)
async def create_topic(topic: TopicCreate, background: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_topic = Topic(**topic.model_dump())
    db.add(db_topic)
    await db.commit()
    await db.refresh(db_topic)
    _schedule_refresh(str(db_topic.id), background)
    return db_topic


@router.get("/", response_model=List[TopicOut])
async def list_topics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Topic).order_by(Topic.updated_at.desc()))
    return result.scalars().all()


@router.get("/{topic_id}", response_model=TopicOut)
async def get_topic(topic_id: UUID, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.put("/{topic_id}", response_model=TopicOut)
async def update_topic(topic_id: UUID, update: TopicUpdate, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    await db.commit()
    await db.refresh(topic)
    return topic


@router.delete("/{topic_id}")
async def delete_topic(topic_id: UUID, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    await db.delete(topic)
    await db.commit()
    return {"message": "Deleted"}


@router.post("/{topic_id}/refresh")
async def refresh_topic_now(topic_id: UUID, background: BackgroundTasks):
    mode = _schedule_refresh(str(topic_id), background)
    return {
        "message": "Refresh queued",
        "mode": mode,
        "refresh_mode_setting": settings.refresh_mode,
    }

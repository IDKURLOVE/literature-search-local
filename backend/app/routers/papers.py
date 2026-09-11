from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Paper
from app.schemas import PaperCreate, PaperOut, PaperUpdate

router = APIRouter()


@router.post("/", response_model=PaperOut)
async def create_paper(payload: PaperCreate, db: AsyncSession = Depends(get_db)):
    """Persist a search hit into the library (favorite). Upsert by DOI when present."""
    if payload.doi:
        result = await db.execute(select(Paper).where(Paper.doi == payload.doi))
        existing = result.scalar_one_or_none()
        if existing:
            return existing
    paper = Paper(**payload.model_dump())
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    return paper


@router.get("/", response_model=List[PaperOut])
async def list_papers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Paper).order_by(Paper.created_at.desc()))
    return result.scalars().all()


@router.get("/{paper_id}", response_model=PaperOut)
async def get_paper(paper_id: UUID, db: AsyncSession = Depends(get_db)):
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.put("/{paper_id}", response_model=PaperOut)
async def update_paper(paper_id: UUID, update: PaperUpdate, db: AsyncSession = Depends(get_db)):
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(paper, field, value)
    await db.commit()
    await db.refresh(paper)
    return paper


@router.delete("/{paper_id}")
async def delete_paper(paper_id: UUID, db: AsyncSession = Depends(get_db)):
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    await db.delete(paper)
    await db.commit()
    return {"message": "Deleted"}

from typing import Iterable, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Paper
from app.schemas import ExportRequest, ExportResponse

router = APIRouter()


def _author_names(paper: Paper) -> List[str]:
    names = []
    for a in paper.authors or []:
        if isinstance(a, dict):
            names.append(a.get("name") or "")
        else:
            names.append(str(a))
    return [n for n in names if n]


def _to_bibtex(papers: Iterable[Paper]) -> str:
    lines: List[str] = []
    for i, p in enumerate(papers):
        key = f"paper{i + 1}"
        authors = " and ".join(_author_names(p))
        lines.append(f"@article{{{key},")
        lines.append(f"  title={{{p.title}}},")
        if authors:
            lines.append(f"  author={{{authors}}},")
        if p.year:
            lines.append(f"  year={{{p.year}}},")
        if p.venue:
            lines.append(f"  journal={{{p.venue}}},")
        if p.doi:
            lines.append(f"  doi={{{p.doi}}},")
        lines.append("}")
    return "\n".join(lines)


def _to_ris(papers: Iterable[Paper]) -> str:
    lines: List[str] = []
    for p in papers:
        lines.append("TY  - JOUR")
        lines.append(f"TI  - {p.title}")
        for name in _author_names(p):
            lines.append(f"AU  - {name}")
        if p.year:
            lines.append(f"PY  - {p.year}")
        if p.venue:
            lines.append(f"JO  - {p.venue}")
        if p.doi:
            lines.append(f"DO  - {p.doi}")
        lines.append("ER  - ")
        lines.append("")
    return "\n".join(lines)


def _to_plain(papers: Iterable[Paper]) -> str:
    lines: List[str] = []
    for p in papers:
        authors = ", ".join(_author_names(p))
        lines.append(f"{authors} ({p.year}). {p.title}. {p.venue or ''}. DOI: {p.doi or 'N/A'}")
    return "\n\n".join(lines)


@router.post("/", response_model=ExportResponse)
async def export_papers(request: ExportRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Paper).where(Paper.id.in_(request.paper_ids)))
    papers = list(result.scalars().all())
    if not papers:
        raise HTTPException(status_code=404, detail="No papers found for given ids")

    if request.format == "bibtex":
        content = _to_bibtex(papers)
    elif request.format == "ris":
        content = _to_ris(papers)
    else:
        content = _to_plain(papers)
    return ExportResponse(content=content, format=request.format)

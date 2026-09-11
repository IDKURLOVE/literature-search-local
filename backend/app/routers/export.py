from collections import defaultdict
from typing import Dict, Iterable, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Paper
from app.schemas import ExportRequest, ExportResponse

router = APIRouter()

UNGROUPED = "未分类"


def _author_names(paper: Paper) -> List[str]:
    names = []
    for a in paper.authors or []:
        if isinstance(a, dict):
            names.append(a.get("name") or "")
        else:
            names.append(str(a))
    return [n for n in names if n]


def _year_key(paper: Paper) -> tuple:
    # newest first; missing year last
    y = paper.year if paper.year is not None else -1
    return (-y, paper.title or "")


def _to_bibtex(papers: Iterable[Paper], key_prefix: str = "") -> List[str]:
    lines: List[str] = []
    for i, p in enumerate(papers):
        key = f"{key_prefix}paper{i + 1}" if key_prefix else f"paper{i + 1}"
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
        if p.tags:
            lines.append(f"  keywords={{{', '.join(p.tags)}}},")
        lines.append("}")
    return lines


def _to_ris(papers: Iterable[Paper]) -> List[str]:
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
    return lines


def _to_plain(papers: Iterable[Paper]) -> List[str]:
    lines: List[str] = []
    for p in papers:
        authors = ", ".join(_author_names(p))
        lines.append(f"{authors} ({p.year}). {p.title}. {p.venue or ''}. DOI: {p.doi or 'N/A'}")
    return lines


def _topic_names(paper: Paper) -> List[str]:
    names = []
    for t in paper.topics or []:
        name = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else None)
        if name:
            names.append(str(name))
    return names


def _group_papers(papers: List[Paper]) -> List[tuple[str, List[Paper]]]:
    """Group by research topic name. A paper in multiple topics appears in each."""
    buckets: Dict[str, List[Paper]] = defaultdict(list)
    assigned = set()
    for p in papers:
        names = _topic_names(p)
        if not names:
            continue
        for name in names:
            buckets[name].append(p)
            assigned.add(p.id)
    for p in papers:
        if p.id not in assigned:
            buckets[UNGROUPED].append(p)

    def group_key(item):
        name, _ = item
        return (name == UNGROUPED, name)

    result = []
    for name, items in sorted(buckets.items(), key=group_key):
        items_sorted = sorted(items, key=_year_key)
        result.append((name, items_sorted))
    return result


def _render_grouped(groups: List[tuple[str, List[Paper]]], fmt: str) -> str:
    blocks: List[str] = []
    counter = 0
    for name, items in groups:
        header = f"# {name}" if fmt == "plain" else f"% ===== {name} ====="
        body_lines: List[str] = []
        if fmt == "bibtex":
            for p in items:
                counter += 1
                body_lines.extend(_to_bibtex([p], key_prefix=f"{_slug(name)}{counter}_"))
        elif fmt == "ris":
            for p in items:
                counter += 1
                body_lines.append(f"DB  - {name}")
                body_lines.extend(_to_ris([p]))
        else:
            body_lines.extend(_to_plain(items))
            body_lines.append("")
        blocks.append(header + "\n" + "\n".join(body_lines))
    return "\n\n".join(blocks).strip() + "\n"


def _slug(text: str) -> str:
    import re

    s = re.sub(r"[^A-Za-z0-9]+", "", text)[:24]
    return s or "topic"


@router.post("/", response_model=ExportResponse)
async def export_papers(request: ExportRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Paper)
        .options(selectinload(Paper.topics))
        .where(Paper.id.in_(request.paper_ids))
    )
    papers = list(result.scalars().all())
    if not papers:
        raise HTTPException(status_code=404, detail="No papers found for given ids")

    # newest first globally as well
    papers.sort(key=_year_key)

    if not request.group_by_topic:
        if request.format == "bibtex":
            content = "\n".join(_to_bibtex(papers))
        elif request.format == "ris":
            content = "\n".join(_to_ris(papers))
        else:
            content = "\n\n".join(_to_plain(papers))
        return ExportResponse(content=content, format=request.format, groups=[])

    groups = _group_papers(papers)
    content = _render_grouped(groups, request.format)
    return ExportResponse(
        content=content,
        format=request.format,
        groups=[name for name, _ in groups],
    )

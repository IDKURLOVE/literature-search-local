import asyncio
import uuid
from typing import Any, Dict, List

from app.models import surname_lower
from app.query_bridge import TranslatedQuery, translate_wos_query
from app.relevance import rank_and_filter
from app.schemas import PaperCreate, SearchRequest
from app.sources import arxiv, crossref, openalex, pubmed, semantic_scholar

SOURCE_MAP = {
    "crossref": crossref.search,
    "openalex": openalex.search,
    "semantic_scholar": semantic_scholar.search,
    "pubmed": pubmed.search,
    "arxiv": arxiv.search,
}


def normalize_title(title: str) -> str:
    import re

    title = (title or "").lower()
    title = re.sub(r"[^\w\s]", "", title, flags=re.UNICODE)
    title = re.sub(r"\s+", " ", title).strip()
    stop_words = {"the", "a", "an", "in", "on", "of", "and", "or", "for", "with"}
    words = [w for w in title.split() if w not in stop_words]
    return " ".join(words)


def deduplicate_papers(papers: List[PaperCreate]) -> List[PaperCreate]:
    seen_doi: Dict[str, bool] = {}
    seen_fingerprint: Dict[str, bool] = {}
    result: List[PaperCreate] = []

    for paper in papers:
        if paper.doi:
            doi_norm = paper.doi.lower().strip()
            if doi_norm in seen_doi:
                continue
            seen_doi[doi_norm] = True
            result.append(paper)
            continue

        title_norm = normalize_title(paper.title)
        first_author = surname_lower(paper.authors[0].name) if paper.authors else ""
        fingerprint = f"{title_norm}|{first_author}|{paper.year}"
        if fingerprint in seen_fingerprint:
            continue
        seen_fingerprint[fingerprint] = True
        result.append(paper)

    return result


def synthetic_paper_id(paper: PaperCreate) -> uuid.UUID:
    if paper.doi:
        return uuid.uuid5(uuid.NAMESPACE_URL, f"doi:{paper.doi.lower().strip()}")
    key = f"title:{normalize_title(paper.title)}|{paper.year}|{surname_lower(paper.authors[0].name) if paper.authors else ''}"
    return uuid.uuid5(uuid.NAMESPACE_URL, key)


async def search_all(request: SearchRequest) -> Dict[str, Any]:
    translated: TranslatedQuery = translate_wos_query(request.query, request.filters)

    tasks = []
    selected = [s for s in request.sources if s in SOURCE_MAP]
    # Fetch extra candidates so local relevance filter has room to cut noise
    fetch_limit = min(100, max(request.limit * 3, request.limit))
    fetch_request = request.model_copy(update={"limit": fetch_limit})
    for source in selected:
        tasks.append(SOURCE_MAP[source](fetch_request, translated))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_papers: List[PaperCreate] = []
    source_status: Dict[str, Any] = {}
    for source, result in zip(selected, results):
        if isinstance(result, Exception):
            source_status[source] = {"status": "error", "error": str(result)}
        else:
            source_status[source] = {"status": "ok", "count": len(result)}
            all_papers.extend(result)

    deduped = deduplicate_papers(all_papers)
    ranked = rank_and_filter(deduped, translated.relevance_terms, request.limit)

    hits = []
    for score, paper in ranked:
        payload = paper.model_dump()
        payload["id"] = synthetic_paper_id(paper)
        payload["relevance_score"] = round(score, 2)
        hits.append(payload)

    return {
        "papers": hits,
        "total": len(hits),
        "sources": source_status,
        "query_translation": {
            "free_text": translated.free_text,
            "api_text": translated.api_text,
            "relevance_terms": translated.relevance_terms,
            "from_year": translated.from_year,
            "until_year": translated.until_year,
            "parse_ok": translated.parse_ok,
            "parse_error": translated.parse_error,
        },
        "candidates_before_filter": len(deduped),
    }

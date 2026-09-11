from typing import List

import httpx

from app.config import settings
from app.query_bridge import TranslatedQuery
from app.schemas import Author, PaperCreate, PaperUrls, SearchRequest

BASE_URL = "https://api.crossref.org/works"


def translate_query(request: SearchRequest, translated: TranslatedQuery) -> dict:
    params = {
        "query.bibliographic": translated.free_text or request.query,
        "rows": request.limit,
        "offset": request.offset,
    }
    if settings.crossref_mailto:
        params["mailto"] = settings.crossref_mailto

    filters = []
    from_year = translated.from_year or request.filters.get("from_year")
    until_year = translated.until_year or request.filters.get("until_year")
    if from_year:
        filters.append(f"from-pub-date:{from_year}-01-01")
    if until_year:
        filters.append(f"until-pub-date:{until_year}-12-31")
    if filters:
        params["filter"] = ",".join(filters)
    return params


async def search(request: SearchRequest, translated: TranslatedQuery) -> List[PaperCreate]:
    params = translate_query(request, translated)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    papers: List[PaperCreate] = []
    for item in data.get("message", {}).get("items", []):
        authors = []
        for author in item.get("author", [])[:10]:
            name = f"{author.get('given', '')} {author.get('family', '')}".strip()
            if name:
                authors.append(Author(name=name))

        doi = item.get("DOI")
        year = None
        for key in ("published-print", "published-online", "created"):
            parts = (item.get(key) or {}).get("date-parts") or [[None]]
            candidate = parts[0][0]
            if candidate:
                year = candidate
                break

        papers.append(
            PaperCreate(
                doi=doi,
                title=(item.get("title") or [""])[0] or "Untitled",
                authors=authors,
                abstract=item.get("abstract") or None,
                year=year,
                venue=(item.get("container-title") or [""])[0] or None,
                publication_type=item.get("type"),
                urls=PaperUrls(doi=f"https://doi.org/{doi}" if doi else None),
                citation_count=item.get("is-referenced-by-count", 0),
                source_apis=["crossref"],
                is_open_access=bool((item.get("open-access") or {}).get("bool", False)),
            )
        )
    return papers

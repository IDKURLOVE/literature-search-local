from typing import Any, Dict, List, Optional

import httpx

from app.query_bridge import TranslatedQuery
from app.schemas import Author, PaperCreate, PaperUrls, SearchRequest

BASE_URL = "https://api.openalex.org/works"


def abstract_from_inverted(index: Optional[Dict[Any, Any]]) -> Optional[str]:
    """OpenAlex returns abstract_inverted_index; rebuild ordered abstract text."""
    if not index:
        return None
    positioned = []
    for word, positions in index.items():
        for pos in positions or []:
            positioned.append((int(pos), str(word)))
    if not positioned:
        return None
    positioned.sort(key=lambda x: x[0])
    return " ".join(word for _, word in positioned)


def translate_query(request: SearchRequest, translated: TranslatedQuery) -> dict:
    page_size = max(request.limit, 1)
    params = {
        "search": translated.free_text or request.query,
        "per-page": page_size,
        "page": (request.offset // page_size) + 1,
    }
    filters = []
    from_year = translated.from_year or request.filters.get("from_year")
    until_year = translated.until_year or request.filters.get("until_year")
    if from_year:
        filters.append(f"publication_year:>={from_year}")
    if until_year:
        filters.append(f"publication_year:<={until_year}")
    if request.filters.get("open_access_only"):
        filters.append("is_oa:true")
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
    for item in data.get("results", []):
        authors = []
        for authorship in item.get("authorships", [])[:10]:
            author = authorship.get("author") or {}
            name = author.get("display_name")
            if name:
                authors.append(Author(name=name))

        ids = item.get("ids") or {}
        doi = ids.get("doi")
        primary = (item.get("primary_location") or {}) or {}
        source = primary.get("source") or {}

        papers.append(
            PaperCreate(
                doi=doi.split("https://doi.org/")[-1] if doi else None,
                title=item.get("display_name") or "Untitled",
                authors=authors,
                abstract=abstract_from_inverted(item.get("abstract_inverted_index")),
                year=item.get("publication_year"),
                venue=source.get("display_name"),
                publication_type=item.get("type"),
                urls=PaperUrls(
                    doi=doi,
                    source=item.get("id"),
                ),
                citation_count=item.get("cited_by_count", 0),
                source_apis=["openalex"],
                is_open_access=bool((item.get("open_access") or {}).get("is_oa", False)),
                open_access_pdf=(item.get("open_access") or {}).get("oa_url"),
            )
        )
    return papers

from typing import List

from app.config import settings
from app.query_bridge import TranslatedQuery
from app.schemas import Author, PaperCreate, PaperUrls, SearchRequest
from app.sources.http_util import get_json

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def translate_query(request: SearchRequest, translated: TranslatedQuery) -> dict:
    params = {
        "query": translated.api_text or translated.free_text or request.query,
        "limit": request.limit,
        "offset": request.offset,
        "fields": "title,authors,abstract,year,venue,citationCount,openAccessPdf,publicationTypes,externalIds",
    }
    from_year = translated.from_year or request.filters.get("from_year")
    until_year = translated.until_year or request.filters.get("until_year")
    if from_year or until_year:
        fy = from_year or ""
        uy = until_year or ""
        if fy and uy:
            params["year"] = f"{fy}-{uy}"
        elif fy:
            params["year"] = f"{fy}-"
        else:
            params["year"] = f"-{uy}"
    return params


async def search(request: SearchRequest, translated: TranslatedQuery) -> List[PaperCreate]:
    params = translate_query(request, translated)
    headers = {}
    if settings.semantic_scholar_api_key:
        headers["x-api-key"] = settings.semantic_scholar_api_key
    data = await get_json(BASE_URL, params=params, headers=headers)

    papers: List[PaperCreate] = []
    for item in data.get("data", []) or []:
        authors = [Author(name=a.get("name")) for a in (item.get("authors") or [])[:10] if a.get("name")]
        external_ids = item.get("externalIds") or {}
        doi = external_ids.get("DOI")
        paper_id = item.get("paperId")
        oa = item.get("openAccessPdf") or {}
        papers.append(
            PaperCreate(
                doi=doi,
                title=item.get("title") or "Untitled",
                authors=authors,
                abstract=item.get("abstract"),
                year=item.get("year"),
                venue=item.get("venue"),
                publication_type=",".join(item.get("publicationTypes") or []) or None,
                urls=PaperUrls(
                    doi=f"https://doi.org/{doi}" if doi else None,
                    source=f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else None,
                ),
                citation_count=item.get("citationCount") or 0,
                source_apis=["semantic_scholar"],
                is_open_access=bool(oa.get("url")),
                open_access_pdf=oa.get("url"),
            )
        )
    return papers

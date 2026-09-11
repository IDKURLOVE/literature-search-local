from typing import List

from app.config import settings
from app.query_bridge import TranslatedQuery
from app.schemas import Author, PaperCreate, PaperUrls, SearchRequest
from app.sources.http_util import get_json

BASE_URL = "https://api.crossref.org/works"


def translate_query(request: SearchRequest, translated: TranslatedQuery) -> dict:
    # Prefer expanded bilingual text; Crossref ranks bibliographic co-occurrence
    biblio = translated.api_text or translated.free_text or request.query
    params = {
        "query.bibliographic": biblio,
        "rows": request.limit,
        "offset": request.offset,
        "sort": "score",
        "order": "desc",
    }
    # Title-focused queries (TI= or short academic title) also hit query.title
    if translated.title_terms:
        params["query.title"] = " ".join(translated.title_terms)
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
    data = await get_json(BASE_URL, params=params)

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

        abstract = item.get("abstract") or None
        papers.append(
            PaperCreate(
                doi=doi,
                title=(item.get("title") or [""])[0] or "Untitled",
                authors=authors,
                abstract=abstract,
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

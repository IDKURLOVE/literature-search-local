from typing import List

from app.query_bridge import TranslatedQuery
from app.schemas import Author, PaperCreate, PaperUrls, SearchRequest
from app.sources.http_util import get_json

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def translate_query(request: SearchRequest, translated: TranslatedQuery) -> dict:
    term = translated.api_text or translated.free_text or request.query
    from_year = translated.from_year or request.filters.get("from_year")
    until_year = translated.until_year or request.filters.get("until_year")
    if from_year or until_year:
        start = from_year or "1900"
        end = until_year or "3000"
        term = f"({term}) AND {start}:{end}[dp]"
    return {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": request.limit,
        "retstart": request.offset,
    }


async def search(request: SearchRequest, translated: TranslatedQuery) -> List[PaperCreate]:
    params = translate_query(request, translated)
    search_data = await get_json(ESEARCH_URL, params=params)
    ids = (search_data.get("esearchresult") or {}).get("idlist") or []
    if not ids:
        return []

    summary_data = await get_json(
        ESummary_URL,
        params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
    )

    papers: List[PaperCreate] = []
    result = summary_data.get("result") or {}
    for uid in result.get("uids") or []:
        item = result.get(uid) or {}
        authors = [Author(name=a.get("name")) for a in (item.get("authors") or [])[:10] if a.get("name")]
        elocation = (item.get("elocationid") or "").replace("doi: ", "").strip()
        pubdate = item.get("pubdate") or ""
        year = None
        if pubdate:
            head = pubdate.split(" ")[0]
            try:
                year = int(head[:4])
            except ValueError:
                year = None
        papers.append(
            PaperCreate(
                doi=elocation or None,
                title=item.get("title") or "Untitled",
                authors=authors,
                abstract=None,
                year=year,
                venue=item.get("fulljournalname"),
                publication_type=",".join(item.get("pubtype") or []) or None,
                urls=PaperUrls(
                    source=f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    doi=f"https://doi.org/{elocation}" if elocation else None,
                ),
                citation_count=0,
                source_apis=["pubmed"],
                is_open_access=False,
            )
        )
    return papers

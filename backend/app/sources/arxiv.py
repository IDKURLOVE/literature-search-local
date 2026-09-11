from typing import List
from xml.etree import ElementTree as ET

from app.query_bridge import TranslatedQuery
from app.schemas import Author, PaperCreate, PaperUrls, SearchRequest
from app.sources.http_util import get_text

BASE_URL = "https://export.arxiv.org/api/query"


def translate_query(request: SearchRequest, translated: TranslatedQuery) -> dict:
    text = translated.free_text or request.query
    return {
        "search_query": f"all:{text}",
        "start": request.offset,
        "max_results": request.limit,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }


async def search(request: SearchRequest, translated: TranslatedQuery) -> List[PaperCreate]:
    params = translate_query(request, translated)
    xml_data = await get_text(BASE_URL, params=params)

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_data)
    papers: List[PaperCreate] = []

    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns)
        title_text = title.text.strip().replace("\n", " ") if title is not None and title.text else "Untitled"

        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.find("atom:name", ns)
            if name is not None and name.text:
                authors.append(Author(name=name.text))

        summary = entry.find("atom:summary", ns)
        abstract = summary.text if summary is not None and summary.text else None

        id_elem = entry.find("atom:id", ns)
        arxiv_url = id_elem.text if id_elem is not None and id_elem.text else ""

        pdf_link = entry.find("atom:link[@title='pdf']", ns)
        pdf_url = pdf_link.get("href") if pdf_link is not None else None

        published = entry.find("atom:published", ns)
        year = int(published.text[:4]) if published is not None and published.text else None

        papers.append(
            PaperCreate(
                doi=None,
                title=title_text,
                authors=authors[:10],
                abstract=abstract,
                year=year,
                venue="arXiv",
                publication_type="preprint",
                urls=PaperUrls(source=arxiv_url, open_access_pdf=pdf_url),
                citation_count=0,
                source_apis=["arxiv"],
                is_open_access=True,
                open_access_pdf=pdf_url,
            )
        )
    return papers

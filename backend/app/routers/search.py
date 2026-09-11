from fastapi import APIRouter

from app.schemas import SearchRequest, SearchResult
from app.sources import search_all

router = APIRouter()


@router.post("/", response_model=SearchResult)
async def search(request: SearchRequest) -> SearchResult:
    raw = await search_all(request)
    return SearchResult(
        papers=raw["papers"],
        total=raw["total"],
        sources=raw["sources"],
        query_translation=raw.get("query_translation"),
    )

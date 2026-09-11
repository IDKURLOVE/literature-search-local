import asyncio
import sys

sys.path.insert(0, "backend")

from app.schemas import SearchRequest
from app.sources import search_all


async def main() -> None:
    req = SearchRequest(query="机器学习预测风速", sources=["crossref", "openalex"], limit=12)
    result = await search_all(req)
    print("TOTAL", result["total"], "CAND", result.get("candidates_before_filter"))
    print("TERMS", result["query_translation"]["relevance_terms"])
    print("API", result["query_translation"]["api_text"])
    for p in result["papers"]:
        print(round(p.get("relevance_score") or 0, 1), p["title"][:100])


if __name__ == "__main__":
    asyncio.run(main())

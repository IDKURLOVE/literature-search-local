import asyncio
import sys

sys.path.insert(0, "backend")

from app.schemas import SearchRequest
from app.sources import search_all


async def main() -> None:
    for q in ("机器学习预测风速", "wind speed prediction", "风速预测"):
        req = SearchRequest(
            query=q,
            sources=["crossref", "openalex", "arxiv"],
            limit=15,
        )
        result = await search_all(req)
        print("=" * 60)
        print("QUERY", q)
        print("TOTAL", result["total"], "CAND", result.get("candidates_before_filter"))
        print("API", result["query_translation"]["api_text"][:120])
        print("SOURCES", result["sources"])
        for p in result["papers"][:8]:
            t = (p.get("title") or "")[:90]
            print(f"  {p.get('year') or '----'}  [{p.get('relevance_score')}] {t}")


if __name__ == "__main__":
    asyncio.run(main())

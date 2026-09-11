import asyncio
import json
import sys

sys.path.insert(0, "backend")

from app.schemas import SearchRequest  # noqa: E402
from app.sources import search_all  # noqa: E402


async def main() -> None:
    req = SearchRequest(
        query='TI="attention is all you need"',
        sources=["openalex", "crossref", "arxiv"],
        limit=3,
    )
    result = await search_all(req)
    print("TOTAL", result["total"])
    print("SOURCES", json.dumps(result["sources"], ensure_ascii=False))
    print("TRANSLATION", json.dumps(result["query_translation"], ensure_ascii=False))
    for p in result["papers"][:5]:
        title = (p.get("title") or "")[:90]
        print("PAPER", title, "|", p.get("doi"), "|", ",".join(p.get("source_apis") or []))


if __name__ == "__main__":
    asyncio.run(main())

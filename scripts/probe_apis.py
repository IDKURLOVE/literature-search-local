import asyncio
import sys

sys.path.insert(0, "backend")
import httpx  # noqa: E402


async def main() -> None:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        urls = [
            "https://export.arxiv.org/api/query?search_query=all:attention&max_results=1",
            "http://export.arxiv.org/api/query?search_query=all:attention&max_results=1",
            "https://api.openalex.org/works?search=attention&per-page=1&mailto=test@example.com",
            "https://api.crossref.org/works?query.bibliographic=attention&rows=1&mailto=test@example.com",
        ]
        for url in urls:
            try:
                r = await client.get(url, headers={"User-Agent": "LitScopeLocal/1.0 (mailto:test@example.com)"})
                print(r.status_code, url[:80], "len", len(r.text))
            except Exception as exc:
                print("ERR", type(exc).__name__, exc, url[:80])


if __name__ == "__main__":
    asyncio.run(main())

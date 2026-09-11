from typing import Any, Dict, Optional

import httpx

from app.config import settings

DEFAULT_TIMEOUT = 30.0


def user_agent() -> str:
    mail = settings.crossref_mailto or "litscope-local@example.com"
    return f"LitScopeLocal/1.0 (mailto:{mail})"


def polite_params(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = dict(extra or {})
    if settings.crossref_mailto:
        params.setdefault("mailto", settings.crossref_mailto)
    return params


def raise_with_context(resp: httpx.Response) -> None:
    if resp.status_code < 400:
        return
    body = (resp.text or "")[:200].strip()
    detail = f"HTTP {resp.status_code} for {resp.request.url}"
    if body:
        detail = f"{detail}: {body}"
    elif resp.status_code == 429:
        detail = f"{detail}: rate limited, retry later or add mailto/API key"
    resp.raise_for_status()
    raise httpx.HTTPStatusError(detail, request=resp.request, response=resp)


async def get_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
    merged = {"User-Agent": user_agent(), **(headers or {})}
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, headers=merged, follow_redirects=True) as client:
        resp = await client.get(url, params=params)
        raise_with_context(resp)
        return resp.json()


async def get_text(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> str:
    merged = {"User-Agent": user_agent(), **(headers or {})}
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, headers=merged, follow_redirects=True) as client:
        resp = await client.get(url, params=params)
        raise_with_context(resp)
        return resp.text

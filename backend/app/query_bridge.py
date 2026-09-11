from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import re

from app.relevance import api_query_text, extract_terms
from app.search import BoolOp, FieldCondition, NearOp, Node, QueryParseError, WOSQueryParser


@dataclass
class TranslatedQuery:
    free_text: str
    from_year: Optional[int] = None
    until_year: Optional[int] = None
    title_terms: List[str] = field(default_factory=list)
    author_terms: List[str] = field(default_factory=list)
    abstract_terms: List[str] = field(default_factory=list)
    venue_terms: List[str] = field(default_factory=list)
    doi: Optional[str] = None
    parse_ok: bool = True
    parse_error: Optional[str] = None
    # Chinese/English keywords used for local relevance ranking
    relevance_terms: List[str] = field(default_factory=list)
    # Text sent to academic APIs (expanded)
    api_text: str = ""


def _parse_year_range(value: str) -> tuple[Optional[int], Optional[int]]:
    value = value.strip()
    if not value:
        return None, None
    if "-" in value:
        left, right = value.split("-", 1)
        try:
            fy = int(left) if left.strip() else None
        except ValueError:
            fy = None
        try:
            uy = int(right) if right.strip() else None
        except ValueError:
            uy = None
        return fy, uy
    try:
        year = int(value)
        return year, year
    except ValueError:
        return None, None


def _collect_terms(node: Node, out: Dict[str, Set[str]], years: List[tuple[Optional[int], Optional[int]]]) -> None:
    if isinstance(node, FieldCondition):
        field = node.field
        value = node.value.strip()
        if not value:
            return
        if field == "year":
            years.append(_parse_year_range(value))
            return
        if field == "doi":
            out["doi"].add(value)
            return
        key = {
            "title": "title",
            "author": "author",
            "abstract": "abstract",
            "venue": "venue",
            "topic": "topic",
            "all": "topic",
            "issn": "topic",
        }.get(field, "topic")
        out[key].add(value)
        return
    if isinstance(node, BoolOp):
        _collect_terms(node.left, out, years)
        _collect_terms(node.right, out, years)
        return
    if isinstance(node, NearOp):
        _collect_terms(node.left, out, years)
        _collect_terms(node.right, out, years)
        return


def translate_wos_query(raw_query: str, extra_filters: Optional[Dict[str, Any]] = None) -> TranslatedQuery:
    extra_filters = extra_filters or {}
    raw = (raw_query or "").strip()
    result = TranslatedQuery(free_text=raw)

    # Always extract Chinese/English terms for ranking (works for plain keywords too)
    result.relevance_terms = extract_terms(raw)
    result.api_text = api_query_text(result.relevance_terms, raw)

    try:
        ast = WOSQueryParser().parse(raw)
    except QueryParseError as exc:
        # Plain keywords are valid queries; mark parse_ok=False only for broken field syntax
        looks_like_field = bool(re.search(r"\b[A-Z]{2}=", raw))
        result.parse_ok = not looks_like_field
        result.parse_error = str(exc) if looks_like_field else None
        result.free_text = result.api_text or raw
        result.from_year = extra_filters.get("from_year")
        result.until_year = extra_filters.get("until_year")
        return result

    buckets: Dict[str, Set[str]] = {
        "title": set(),
        "author": set(),
        "abstract": set(),
        "venue": set(),
        "topic": set(),
        "doi": set(),
    }
    years: List[tuple[Optional[int], Optional[int]]] = []
    _collect_terms(ast, buckets, years)

    fy, uy = None, None
    for a, b in years:
        if a is not None:
            fy = a if fy is None else min(fy, a)
        if b is not None:
            uy = b if uy is None else max(uy, b)

    result.from_year = extra_filters.get("from_year", fy)
    result.until_year = extra_filters.get("until_year", uy)
    result.title_terms = sorted(buckets["title"])
    result.author_terms = sorted(buckets["author"])
    result.abstract_terms = sorted(buckets["abstract"])
    result.venue_terms = sorted(buckets["venue"])
    result.doi = next(iter(buckets["doi"]), None)

    free_parts: List[str] = []
    free_parts.extend(result.title_terms)
    free_parts.extend(result.abstract_terms)
    free_parts.extend(result.author_terms)
    free_parts.extend(result.venue_terms)
    free_parts.extend(sorted(buckets["topic"]))
    if result.doi:
        free_parts.append(result.doi)
    structured = " ".join(dict.fromkeys(p for p in free_parts if p))
    result.free_text = structured or result.api_text or raw

    # Merge structured field terms into relevance set
    extra = extract_terms(structured)
    for t in extra:
        if t not in result.relevance_terms:
            result.relevance_terms.append(t)
    result.api_text = api_query_text(result.relevance_terms, result.free_text)
    return result

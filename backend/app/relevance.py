"""Query tokenization + relevance ranking for multi-source search.

Handles Chinese academic phrases (without spaces) via a small lexicon +
English expansion so Crossref/OpenAlex results can be filtered to the topic.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence

# Longest-match lexicon for common research Chinese (extend as needed)
_ZH_LEXICON = (
    "机器学习",
    "深度学习",
    "强化学习",
    "迁移学习",
    "联邦学习",
    "神经网络",
    "卷积神经网络",
    "循环神经网络",
    "自然语言处理",
    "知识图谱",
    "风力发电",
    "风电功率",
    "风速预测",
    "风速",
    "风电",
    "风能",
    "功率预测",
    "负荷预测",
    "电力负荷",
    "短期预测",
    "长期预测",
    "时间序列",
    "图像识别",
    "目标检测",
    "语义分割",
    "推荐系统",
    "异常检测",
    "特征选择",
    "超参数",
    "大语言模型",
    "预训练",
    "微调",
    "注意力机制",
    "气象",
    "大气",
    "新能源",
    "光伏发电",
    "光伏",
    "预测",
    "预报",
    "分类",
    "回归",
    "聚类",
    "识别",
    "检测",
    "控制",
    "优化",
    "调度",
    "材料",
    "性能",
    "教学",
)

_ZH_EN = {
    "机器学习": ["machine learning", "ML"],
    "深度学习": ["deep learning"],
    "强化学习": ["reinforcement learning"],
    "迁移学习": ["transfer learning"],
    "联邦学习": ["federated learning"],
    "神经网络": ["neural network"],
    "卷积神经网络": ["convolutional neural network", "CNN"],
    "循环神经网络": ["recurrent neural network", "RNN"],
    "自然语言处理": ["natural language processing", "NLP"],
    "知识图谱": ["knowledge graph"],
    "风力发电": ["wind power"],
    "风电功率": ["wind power"],
    "风速预测": ["wind speed prediction", "wind speed forecasting"],
    "风速": ["wind speed"],
    "风电": ["wind power", "wind energy"],
    "风能": ["wind energy"],
    "功率预测": ["power prediction", "power forecasting"],
    "负荷预测": ["load forecasting", "load prediction"],
    "电力负荷": ["power load", "electric load"],
    "短期预测": ["short-term forecasting", "short-term prediction"],
    "长期预测": ["long-term forecasting"],
    "时间序列": ["time series"],
    "图像识别": ["image recognition"],
    "目标检测": ["object detection"],
    "语义分割": ["semantic segmentation"],
    "推荐系统": ["recommender system", "recommendation system"],
    "异常检测": ["anomaly detection"],
    "大语言模型": ["large language model", "LLM"],
    "预训练": ["pretraining", "pre-training"],
    "微调": ["fine-tuning", "finetuning"],
    "注意力机制": ["attention mechanism"],
    "气象": ["meteorological", "weather"],
    "大气": ["atmospheric", "atmosphere"],
    "新能源": ["renewable energy"],
    "光伏发电": ["photovoltaic", "PV power"],
    "光伏": ["photovoltaic", "solar"],
    "预测": ["prediction", "forecasting", "forecast"],
    "预报": ["forecast", "forecasting"],
    "材料": ["material"],
    "性能": ["performance", "property"],
}

_EN_STOP = {
    "the",
    "a",
    "an",
    "of",
    "and",
    "or",
    "for",
    "in",
    "on",
    "to",
    "with",
    "based",
    "using",
    "via",
}

_HTML_TAG = re.compile(r"<[^>]+>")


def strip_markup(text: Optional[str]) -> str:
    if not text:
        return ""
    return _HTML_TAG.sub(" ", text)


def _segment_chinese(chunk: str) -> List[str]:
    """Greedy longest-match against lexicon; leftovers become 2-char grams."""
    terms: List[str] = []
    i = 0
    n = len(chunk)
    while i < n:
        matched = None
        for word in sorted(_ZH_LEXICON, key=len, reverse=True):
            if chunk.startswith(word, i):
                matched = word
                break
        if matched:
            terms.append(matched)
            i += len(matched)
        else:
            if i + 2 <= n:
                terms.append(chunk[i : i + 2])
                i += 2
            else:
                terms.append(chunk[i])
                i += 1
    return terms


def extract_terms(raw_query: str) -> List[str]:
    """Extract Chinese phrases + English words from a free-text or WOS query."""
    text = raw_query or ""
    # drop field tags like TI= AU=
    text = re.sub(r"\b[A-Z]{2}=", " ", text)
    text = re.sub(r'"([^"]*)"', r" \1 ", text)
    text = re.sub(r"[()]", " ", text)
    text = re.sub(r"\b(AND|OR|NOT|NEAR/\d+)\b", " ", text, flags=re.I)

    terms: List[str] = []
    for eng in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text):
        w = eng.lower()
        if w not in _EN_STOP:
            terms.append(w)

    for chunk in re.findall(r"[一-鿿]+", text):
        terms.extend(_segment_chinese(chunk))

    # unique preserve order
    seen = set()
    out: List[str] = []
    for t in terms:
        t = t.strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def expand_terms_for_apis(terms: Sequence[str]) -> List[str]:
    """Add English expansions for Chinese terms so global APIs can match."""
    expanded: List[str] = []
    seen = set()
    for t in terms:
        for item in (t, *_ZH_EN.get(t, ())):
            key = item.lower()
            if key not in seen:
                seen.add(key)
                expanded.append(item)
    return expanded


def _has_cjk(text: str) -> bool:
    return any("一" <= ch <= "鿿" for ch in text)


def english_only_terms(terms: Sequence[str]) -> List[str]:
    """Map Chinese concepts to English phrases; keep ASCII tokens as-is."""
    out: List[str] = []
    seen = set()
    for t in terms:
        candidates: List[str] = []
        if t.isascii():
            candidates.append(t)
        else:
            candidates.extend(_ZH_EN.get(t, ()))
            # fallback: keep CJK token only if no English mapping (local filter still uses it)
        for c in candidates:
            key = c.lower()
            if key not in seen:
                seen.add(key)
                out.append(c)
    return out


def api_query_text(terms: Sequence[str], fallback: str) -> str:
    """Text sent to Crossref/OpenAlex/S2/arXiv.

    Chinese characters in global APIs hurt recall — when the user typed Chinese,
    prefer English expansions only (e.g. 机器学习预测风速 → machine learning wind speed).
    """
    if not terms:
        return fallback.strip()
    if any(_has_cjk(t) for t in terms):
        eng = english_only_terms(terms)
        if eng:
            return " ".join(eng)
    return " ".join(expand_terms_for_apis(terms))


def _haystack(title: str, abstract: str, venue: str) -> str:
    return f"{title}\n{abstract}\n{venue}".lower()


def score_paper(
    title: str,
    abstract: Optional[str],
    venue: Optional[str],
    terms: Sequence[str],
    year: Optional[int] = None,
) -> float:
    if not terms:
        base = 1.0
    else:
        hay = _haystack(title or "", strip_markup(abstract), venue or "")
        title_l = (title or "").lower()
        base = 0.0
        for t in expand_terms_for_apis(terms):
            tl = t.lower()
            if not tl:
                continue
            if tl in title_l:
                base += 3.0
            elif tl in hay:
                base += 1.0
    # mild recency boost so newer on-topic papers win ties (WOS-like freshness)
    if year is not None:
        if year >= 2022:
            base += 1.5
        elif year >= 2018:
            base += 0.8
        elif year >= 2015:
            base += 0.3
    return base


def is_relevant(
    title: str,
    abstract: Optional[str],
    venue: Optional[str],
    terms: Sequence[str],
) -> bool:
    """Multi-concept queries must hit the object term (last) + at least one other concept."""
    if not terms:
        return True
    hay = _haystack(title or "", strip_markup(abstract), venue or "")

    def concept_hit(term: str) -> bool:
        return any(t.lower() in hay for t in expand_terms_for_apis([term]))

    if len(terms) == 1:
        return concept_hit(terms[0])
    if len(terms) == 2:
        return concept_hit(terms[0]) and concept_hit(terms[1])

    if not concept_hit(terms[-1]):
        return False
    return any(concept_hit(t) for t in terms[:-1])


def rank_and_filter(
    papers: Iterable,
    terms: Sequence[str],
    limit: int,
):
    """Score, hard-filter, then adaptively relax so recall is not near-zero."""
    limit = max(limit, 1)
    scored_all = []
    for p in papers:
        s = score_paper(p.title, p.abstract, p.venue, terms, getattr(p, "year", None))
        rel = is_relevant(p.title, p.abstract, p.venue, terms)
        scored_all.append((s, p, rel))

    def sort_key(item):
        s, p = item[0], item[1]
        return (-s, -(p.year or 0), p.title or "")

    hard = [(s, p) for s, p, rel in scored_all if rel]
    hard.sort(key=sort_key)
    # If hard filter leaves too few (or nothing), keep any positive-score hits
    if len(hard) >= min(limit, 3):
        return hard[:limit]

    soft = [(s, p) for s, p, _ in scored_all if s > 0]
    soft.sort(key=sort_key)
    if soft:
        return soft[:limit]

    everything = [(s, p) for s, p, _ in scored_all]
    everything.sort(key=sort_key)
    return everything[:limit]

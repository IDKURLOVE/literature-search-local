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


def api_query_text(terms: Sequence[str], fallback: str) -> str:
    expanded = expand_terms_for_apis(terms)
    if not expanded:
        return fallback.strip()
    # Prefer AND-like concatenation for multi-term topics (Crossref/OpenAlex rank by co-occurrence)
    return " ".join(expanded)


def _haystack(title: str, abstract: str, venue: str) -> str:
    return f"{title}\n{abstract}\n{venue}".lower()


def score_paper(title: str, abstract: Optional[str], venue: Optional[str], terms: Sequence[str]) -> float:
    if not terms:
        return 1.0
    hay = _haystack(title or "", strip_markup(abstract), venue or "")
    title_l = (title or "").lower()
    score = 0.0
    for t in expand_terms_for_apis(terms):
        tl = t.lower()
        if not tl:
            continue
        if tl in title_l:
            score += 3.0
        elif tl in hay:
            score += 1.0
    return score


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

    # 3+ terms e.g. 机器学习 / 预测 / 风速 → require object (last) + any other
    if not concept_hit(terms[-1]):
        return False
    return any(concept_hit(t) for t in terms[:-1])


def rank_and_filter(
    papers: Iterable,
    terms: Sequence[str],
    limit: int,
):
    """Return (kept_papers_with_score) sorted by score desc, relevance filtered."""
    scored = []
    for p in papers:
        s = score_paper(p.title, p.abstract, p.venue, terms)
        if is_relevant(p.title, p.abstract, p.venue, terms):
            scored.append((s, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[: max(limit, 1)]

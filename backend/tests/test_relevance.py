from app.relevance import (
    api_query_text,
    extract_terms,
    is_relevant,
    rank_and_filter,
    score_paper,
)
from app.schemas import Author, PaperCreate


def test_extract_chinese_terms():
    terms = extract_terms("机器学习预测风速")
    assert "机器学习" in terms
    assert "风速" in terms
    assert "预测" in terms


def test_extract_english_and_wos():
    terms = extract_terms('TI="large language model" AND PY=2023')
    assert "large" in terms or "language" in terms


def test_relevance_keeps_on_topic():
    terms = extract_terms("机器学习预测风速")
    good = PaperCreate(
        title="基于机器学习的风速预测方法研究",
        abstract="本文提出一种机器学习风速预测模型",
        authors=[Author(name="Zhang")],
        source_apis=["test"],
    )
    bad = PaperCreate(
        title="Machine Learning-Based Approach to Early Diabetes Risk Prediction",
        abstract="diabetes risk prediction",
        authors=[Author(name="Smith")],
        source_apis=["test"],
    )
    assert is_relevant(good.title, good.abstract, good.venue, terms)
    assert not is_relevant(bad.title, bad.abstract, bad.venue, terms)
    assert score_paper(good.title, good.abstract, good.venue, terms) > score_paper(
        bad.title, bad.abstract, bad.venue, terms
    )


def test_rank_and_filter_limit():
    terms = extract_terms("风速预测")
    papers = [
        PaperCreate(title=f"风速预测研究 {i}", abstract="风速", source_apis=["t"]) for i in range(5)
    ] + [
        PaperCreate(title="完全无关的教育学论文", abstract="教学", source_apis=["t"])
    ]
    ranked = rank_and_filter(papers, terms, limit=3)
    assert len(ranked) <= 3
    for _, p in ranked:
        assert "风速" in (p.title or "") or "风速" in (p.abstract or "")


def test_multi_concept_requires_object_term():
    terms = extract_terms("机器学习预测风速")
    assert "风速" in terms
    load_paper = PaperCreate(
        title="基于机器学习的电力负荷预测方法研究",
        abstract="机器学习 负荷预测",
        source_apis=["t"],
    )
    wind_paper = PaperCreate(
        title="基于机器学习的风速预测",
        abstract="机器学习 风速",
        source_apis=["t"],
    )
    assert not is_relevant(load_paper.title, load_paper.abstract, load_paper.venue, terms)
    assert is_relevant(wind_paper.title, wind_paper.abstract, wind_paper.venue, terms)


def test_api_text_prefers_english_for_chinese_query():
    terms = extract_terms("机器学习预测风速")
    text = api_query_text(terms, "机器学习预测风速")
    assert "machine learning" in text.lower()
    assert "wind speed" in text.lower()
    # should not send raw CJK to global APIs
    assert "机器学习" not in text


def test_adaptive_filter_keeps_positive_scores_when_hard_filter_empty():
    # English-only papers that cannot match Chinese object term 风速 literally,
    # but have English expansions → hard filter may be empty; soft path keeps them.
    terms = extract_terms("机器学习预测风速")
    en = PaperCreate(
        title="Machine learning for wind speed forecasting: a review",
        abstract="wind speed prediction using machine learning",
        year=2025,
        source_apis=["t"],
    )
    ranked = rank_and_filter([en], terms, limit=5)
    assert ranked, "adaptive fallback should keep on-topic English paper"
    assert "wind speed" in ranked[0][1].title.lower()

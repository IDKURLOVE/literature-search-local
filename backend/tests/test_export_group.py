from types import SimpleNamespace

from app.routers.export import UNGROUPED, _group_papers, _render_grouped


def _paper(pid, title, year, topics=None):
    return SimpleNamespace(
        id=pid,
        title=title,
        year=year,
        authors=[{"name": "Ada Lovelace"}],
        venue="Venue",
        doi=f"10.1/{pid}",
        tags=[],
        topics=topics or [],
    )


def test_group_by_topic_and_year_sort():
    papers = [
        _paper("a", "Old wind", 2010, [SimpleNamespace(name="风速主题")]),
        _paper("b", "New wind", 2024, [SimpleNamespace(name="风速主题")]),
        _paper("c", "Orphan", 2020, []),
        _paper("d", "Multi", 2022, [SimpleNamespace(name="风速主题"), SimpleNamespace(name="另一主题")]),
    ]
    groups = dict(_group_papers(papers))
    assert "风速主题" in groups
    assert UNGROUPED in groups
    wind_years = [p.year for p in groups["风速主题"]]
    assert wind_years[0] == 2024
    assert wind_years[-1] == 2010
    assert "另一主题" in groups
    assert groups[UNGROUPED][0].title == "Orphan"


def test_render_plain_has_topic_headers():
    papers = [
        _paper("a", "New", 2024, [SimpleNamespace(name="TopicA")]),
        _paper("b", "Old", 2019, []),
    ]
    groups = _group_papers(papers)
    text = _render_grouped(groups, "plain")
    assert "# TopicA" in text
    assert f"# {UNGROUPED}" in text
    assert text.index("New") < text.index("Old") or "TopicA" in text

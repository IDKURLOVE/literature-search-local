from app.routers.export import _to_bibtex, _to_plain, _to_ris
from app.schemas import Author, PaperCreate
from app.sources import deduplicate_papers, normalize_title, synthetic_paper_id
from app.sources.openalex import abstract_from_inverted
from app.models import Paper


def test_openalex_abstract_from_inverted_index():
    inverted = {"Hello": [0], "world": [1], "from": [2], "OpenAlex": [3]}
    assert abstract_from_inverted(inverted) == "Hello world from OpenAlex"
    assert abstract_from_inverted(None) is None
    assert abstract_from_inverted({}) is None


def _paper(title="Deep Learning", doi=None, year=2020, author="Yann LeCun"):
    return PaperCreate(
        doi=doi,
        title=title,
        authors=[Author(name=author)],
        year=year,
        source_apis=["test"],
    )


def test_dedup_by_doi():
    papers = [
        _paper(title="A", doi="10.1/a"),
        _paper(title="B", doi="10.1/a"),
        _paper(title="C", doi="10.1/c"),
    ]
    out = deduplicate_papers(papers)
    assert len(out) == 2


def test_dedup_by_fingerprint():
    papers = [
        _paper(title="The Deep Learning Book", year=2016),
        _paper(title="Deep Learning Book", year=2016),
    ]
    out = deduplicate_papers(papers)
    assert len(out) == 1


def test_synthetic_id_stable():
    p = _paper(doi="10.1234/abc")
    assert synthetic_paper_id(p) == synthetic_paper_id(_paper(doi="10.1234/ABC"))


def test_normalize_title():
    assert normalize_title("The  Deep-Learning!") == "deeplearning"


def test_export_bibtex_author_join():
    paper = Paper(
        title="Attention Is All You Need",
        authors=[{"name": "Ashish Vaswani"}, {"name": "Noam Shazeer"}],
        year=2017,
        venue="NeurIPS",
        doi="10.5555/3295222",
    )
    content = _to_bibtex([paper])
    assert "Ashish Vaswani and Noam Shazeer" in content
    assert "@article{paper1," in content


def test_export_ris_and_plain():
    paper = Paper(
        title="Test",
        authors=[{"name": "Ada Lovelace"}],
        year=1843,
        venue="Note G",
        doi="10.1/x",
    )
    assert "TY  - JOUR" in _to_ris([paper])
    assert "Ada Lovelace" in _to_plain([paper])

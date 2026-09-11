from app.query_bridge import translate_wos_query
from app.search import QueryParseError, WOSQueryParser
import pytest


def test_parse_simple_field():
    node = WOSQueryParser().parse("TI=transformer")
    assert node.field == "title"
    assert node.value == "transformer"


def test_parse_boolean():
    node = WOSQueryParser().parse("TI=transformer AND PY=2023")
    assert node.op == "AND"


def test_parse_phrase():
    node = WOSQueryParser().parse('TI="large language model"')
    assert node.value == "large language model"


def test_parse_parentheses():
    node = WOSQueryParser().parse('(TI=transformer OR TI=bert) AND PY=2020-2024')
    assert node.op == "AND"


def test_empty_query_raises():
    with pytest.raises(QueryParseError):
        WOSQueryParser().parse("   ")


def test_translate_year_range():
    t = translate_wos_query('TI="large language model" AND PY=2023-2024')
    assert t.parse_ok is True
    assert t.from_year == 2023
    assert t.until_year == 2024
    assert "large language model" in t.free_text


def test_translate_single_year():
    t = translate_wos_query("PY=2021 AND AU=einstein")
    assert t.from_year == 2021
    assert t.until_year == 2021
    assert "einstein" in t.author_terms or "einstein" in t.free_text


def test_translate_invalid_falls_back():
    t = translate_wos_query("TI=", {"from_year": 2019})
    assert t.parse_ok is False
    assert t.from_year == 2019

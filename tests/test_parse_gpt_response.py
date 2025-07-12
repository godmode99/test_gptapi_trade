import pytest

from gpt_trader.parse.parse_gpt_response import _extract_json


def test_extract_json_unfenced():
    text = "Some text {\"a\": 1, \"b\": 2} end"
    assert _extract_json(text) == {"a": 1, "b": 2}


def test_extract_json_fenced_json():
    text = "```json\n{\"a\": 1}\n```"
    assert _extract_json(text) == {"a": 1}


def test_extract_json_fenced_plain():
    text = "```\n{\"a\": 2}\n```"
    assert _extract_json(text) == {"a": 2}


def test_extract_json_missing():
    with pytest.raises(ValueError):
        _extract_json("no json here")


def test_extract_json_multiple_objects():
    text = "first {\"a\": 1} second {\"b\": 2}"
    assert _extract_json(text) == {"a": 1}


def test_extract_json_nested_objects():
    text = "```json\n{\"a\": {\"b\": 2}}\n```"
    assert _extract_json(text) == {"a": {"b": 2}}

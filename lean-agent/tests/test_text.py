import pytest

from lean_agent._text import parse_first_json_object, strip_json_fences


def test_strip_json_fences_removes_opening_and_closing():
    assert strip_json_fences('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_strip_json_fences_handles_no_lang_tag():
    assert strip_json_fences('```\n{"a": 1}\n```') == '{"a": 1}'


def test_strip_json_fences_passthrough_when_no_fences():
    assert strip_json_fences('{"a": 1}') == '{"a": 1}'


def test_parse_first_json_object_clean():
    assert parse_first_json_object('{"a": 1}') == {"a": 1}


def test_parse_first_json_object_with_fences():
    assert parse_first_json_object('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_first_json_object_with_trailing_prose():
    """Real Sonnet appends explanation after the JSON closes. Must be ignored."""
    text = '{"a": 1, "b": [2, 3]}\n\nLet me know if you want me to expand on this.'
    assert parse_first_json_object(text) == {"a": 1, "b": [2, 3]}


def test_parse_first_json_object_with_leading_prose():
    """Some models prepend 'Sure! Here's the JSON:' before opening brace."""
    text = "Sure! Here's the JSON:\n\n" + '{"a": 1}'
    assert parse_first_json_object(text) == {"a": 1}


def test_parse_first_json_object_with_both_prose_and_fences():
    text = "Sure! Here's the analysis:\n\n```json\n" + '{"a": 1}' + "\n```\n\nDone."
    assert parse_first_json_object(text) == {"a": 1}


def test_parse_first_json_object_nested_json():
    text = '{"outer": {"inner": [1, 2, {"deep": true}]}}'
    assert parse_first_json_object(text) == {"outer": {"inner": [1, 2, {"deep": True}]}}


def test_parse_first_json_object_raises_when_no_object():
    with pytest.raises(ValueError, match="no JSON object found"):
        parse_first_json_object("just prose, no JSON here at all")

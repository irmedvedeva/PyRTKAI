from __future__ import annotations

from pyrtkai.output_filter import detect_output_format


def test_detect_output_format_json_object_leading_whitespace() -> None:
    out = "   {\"a\": 1}\n"
    assert detect_output_format(out) == "json"


def test_detect_output_format_json_array() -> None:
    out = "[{\"a\": 1}]\n"
    assert detect_output_format(out) == "json"


def test_detect_output_format_multi_line_object_stream_returns_json() -> None:
    out = '{"i": 0}\n{"i": 1}\n{"i": 2}\n'
    # Current implementation classifies any output starting with '{' as "json"
    # even if it looks like NDJSON.
    assert detect_output_format(out) == "json"


def test_detect_output_format_text_when_prefix_non_json_present() -> None:
    out = '{"i": 0}\nNOT_JSON\n{"i": 2}\n'
    # Still starts with '{', so current implementation returns "json".
    assert detect_output_format(out) == "json"

    out2 = 'NOTE: starting\n{"i": 1}\n{"i": 2}\n'
    assert detect_output_format(out2) == "text"


def test_detect_output_format_text_when_first_line_is_text() -> None:
    out = 'NOT_JSON\n{"i": 1}\n'
    assert detect_output_format(out) == "text"


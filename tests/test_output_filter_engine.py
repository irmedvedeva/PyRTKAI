from __future__ import annotations

import json
from typing import Literal

import pytest

from pyrtkai.contracts import CommandMeta
from pyrtkai.output_filter import (
    TruncatingOutputFilterEngine,
    create_output_filter_engine,
)


def _meta(output_format: Literal["text", "json", "ndjson"]) -> CommandMeta:
    return CommandMeta(
        classification="test", output_format=output_format, did_fail=False
    )


def test_truncation_boundary_no_marker_when_len_equals_max_chars() -> None:
    engine = TruncatingOutputFilterEngine()
    max_chars = engine.max_chars
    out = "A" * max_chars

    res = engine.filter(out, meta=_meta("text"))
    assert res.did_modify is False
    assert engine.trunc_marker not in res.output
    assert res.output == out


def test_truncation_overflow_preserves_head_tail() -> None:
    engine = TruncatingOutputFilterEngine()
    max_chars = engine.max_chars
    out = "A" * (max_chars + 123)

    res = engine.filter(out, meta=_meta("text"))
    assert res.did_modify is True
    assert engine.trunc_marker in res.output

    half = max_chars // 2
    assert res.output.startswith(out[:half])
    assert res.output.endswith(out[-half:])
    assert res.output.count(engine.trunc_marker) == 1


def test_json_pass_through_is_unchanged_even_when_large() -> None:
    engine = TruncatingOutputFilterEngine()
    payload = {"a": "X" * (engine.max_chars * 2)}
    out = json.dumps(payload)

    res = engine.filter(out, meta=_meta("json"))
    assert res.did_modify is False
    assert res.output == out


def test_ndjson_pass_through_is_unchanged_even_when_large() -> None:
    engine = TruncatingOutputFilterEngine()
    lines = [json.dumps({"i": i, "v": "X" * 50}) for i in range(300)]
    out = "\n".join(lines) + "\n"

    res = engine.filter(out, meta=_meta("ndjson"))
    assert res.did_modify is False
    assert res.output == out


def test_output_filter_profile_unknown_falls_back_to_truncating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYRTKAI_OUTPUT_FILTER_PROFILE", "unknown_profile")
    # Factory should still return a truncating engine with defaults.
    engine = create_output_filter_engine()
    assert isinstance(engine, TruncatingOutputFilterEngine)



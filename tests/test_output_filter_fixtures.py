from __future__ import annotations

from pyrtkai.output_filter import TruncatingOutputFilterEngine
from tests.filter_fixture_harness import (
    generate_output_from_case,
    load_output_filter_cases,
    meta_from_output_format,
)


def test_truncating_output_filter_engine_fixture_cases() -> None:
    engine = TruncatingOutputFilterEngine()
    marker = engine.trunc_marker

    for case in load_output_filter_cases():
        out = generate_output_from_case(case)
        meta = meta_from_output_format(case.input_format)
        res = engine.filter(out, meta=meta)

        did_modify = bool(case.expect.get("did_modify", False))
        marker_present = bool(case.expect.get("marker_present", False))
        assert res.did_modify == did_modify

        if case.input_format == "text" and marker_present:
            assert marker in res.output
            # Head+tail invariants for deterministic truncation.
            half = engine.max_chars // 2
            assert res.output.startswith(out[:half])
            assert res.output.endswith(out[-half:])
        elif marker_present:
            # JSON/NDJSON cases: pass-through, marker should never appear.
            assert marker not in res.output

        if bool(case.expect.get("unchanged", False)):
            assert res.output == out


from __future__ import annotations

from pyrtkai.output_filter import create_output_filter_engine
from tests.filter_fixture_harness import (
    generate_output_from_case,
    load_output_filter_cases,
    meta_from_output_format,
)


def test_output_filter_contract_deterministic_and_idempotent() -> None:
    engine = create_output_filter_engine()

    half = engine.max_chars // 2
    for case in load_output_filter_cases():
        out = generate_output_from_case(case)
        meta = meta_from_output_format(case.input_format)

        res1 = engine.filter(out, meta)
        res2 = engine.filter(out, meta)
        assert res1.output == res2.output
        assert res1.did_modify == res2.did_modify

        # Idempotence: applying the same filter again should not change output.
        res3 = engine.filter(res1.output, meta)
        assert res3.output == res1.output

        if case.input_format in {"json", "ndjson"}:
            # Contract: structured output must not be modified by filters in MVP.
            assert res1.did_modify is False
            assert res1.output == out
            continue

        # Text contract: marker+head/tail semantics.
        if len(out) <= engine.max_chars:
            assert res1.did_modify is False
            assert res1.output == out
        else:
            assert res1.did_modify is True
            assert engine.trunc_marker in res1.output
            assert res1.output.startswith(out[:half])
            assert res1.output.endswith(out[-half:])


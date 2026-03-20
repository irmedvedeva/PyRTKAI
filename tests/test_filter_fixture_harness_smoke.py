from __future__ import annotations

from pyrtkai.output_filter import detect_output_format
from tests.filter_fixture_harness import generate_output_from_case, load_output_filter_cases


def test_output_filter_fixture_harness_smoke() -> None:
    cases = load_output_filter_cases()
    assert len(cases) >= 1

    for case in cases:
        out = generate_output_from_case(case)
        assert isinstance(out, str)
        # Basic sanity: detect_output_format returns one of the expected values.
        fmt = detect_output_format(out)
        assert fmt in {"text", "json", "ndjson"}


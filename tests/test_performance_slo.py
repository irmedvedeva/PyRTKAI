"""
Optional proxy overhead SLO checks (enabled with PYRTKAI_ENFORCE_PERF_SLO=1).

Default CI / local `pytest -q` skips these to avoid flaky failures on shared runners.
"""

from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stdout
from typing import Any, cast

import pytest

from pyrtkai.cli import main

# Documented in .doc/13_performance_slo.md
_MAX_PROXY_AVG_MS = 10_000.0
_MAX_RATIO = 80.0


def _bench_payload(*, iters: int = 2) -> dict[str, Any]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(
            [
                "bench",
                "proxy",
                "--iters",
                str(iters),
                "--json",
                sys.executable,
                "-c",
                "pass",
            ]
        )
    assert rc == 0, "bench proxy must succeed for SLO scenario"
    return cast(dict[str, Any], json.loads(buf.getvalue().strip()))


@pytest.mark.skipif(
    os.environ.get("PYRTKAI_ENFORCE_PERF_SLO", "").strip() != "1",
    reason="set PYRTKAI_ENFORCE_PERF_SLO=1 to run proxy SLO tests",
)
def test_slo_proxy_overhead_trivial_child() -> None:
    p = _bench_payload(iters=2)
    assert p["direct_exit_code"] == 0
    assert p["proxy_exit_code"] == 0
    proxy_ms = float(p["proxy_avg_ms"])
    ratio = p["ratio_proxy_to_direct"]
    assert proxy_ms < _MAX_PROXY_AVG_MS, f"proxy_avg_ms={proxy_ms} exceeds {_MAX_PROXY_AVG_MS}"
    assert ratio is not None, "ratio must be computed"
    assert float(ratio) < _MAX_RATIO, f"ratio={ratio} exceeds {_MAX_RATIO}"

from __future__ import annotations

import json

import pytest

from pyrtkai.cli import main


def test_bench_proxy_smoke_json(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(
        [
            "bench",
            "proxy",
            "--iters",
            "2",
            "--json",
            __import__("sys").executable,
            "-c",
            "print('A' * 1000)",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["iters"] == 2
    assert payload["direct_avg_ms"] >= 0
    assert payload["proxy_avg_ms"] >= 0
    assert payload["direct_exit_code"] == 0
    assert payload["proxy_exit_code"] == 0


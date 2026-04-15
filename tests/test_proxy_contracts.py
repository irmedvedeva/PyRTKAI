from __future__ import annotations

import json
import sys

import pytest

from pyrtkai.cli import main


def test_proxy_contract_exit_code_parity(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(
        [
            "proxy",
            sys.executable,
            "-c",
            "import sys; sys.exit(7)",
        ]
    )
    assert rc == 7
    _ = capsys.readouterr()


def test_proxy_contract_json_passthrough(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(
        [
            "proxy",
            sys.executable,
            "-c",
            "import json; print(json.dumps({'ok': True, 'n': 1}))",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out.strip()
    parsed = json.loads(out)
    assert parsed["ok"] is True
    assert parsed["n"] == 1


def test_proxy_contract_summary_signal_shape(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYRTKAI_OUTPUT_MAX_CHARS", "120")
    rc = main(["proxy", "--summary", sys.executable, "-c", "print('x' * 400)"])
    assert rc == 0
    err = capsys.readouterr().err
    assert "[pyrtkai]" in err
    assert "output chars" in err
    assert "saved" in err.lower()
    assert "heuristic; not a model tokenizer" in err

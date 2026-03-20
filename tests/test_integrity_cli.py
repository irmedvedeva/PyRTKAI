from __future__ import annotations

import json
from pathlib import Path

import pytest

from pyrtkai.cli import main
from pyrtkai.integrity import store_sha256_baseline


def test_verify_hook_ok(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    hook_path = tmp_path / "hook.sh"
    baseline_path = tmp_path / ".hook.sha256"
    hook_path.write_text("echo 1\n", encoding="utf-8")
    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)

    rc = main(
        [
            "verify-hook",
            "--hook-path",
            str(hook_path),
            "--baseline-path",
            str(baseline_path),
            "--json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["ok"] is True


def test_verify_hook_tampered_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hook_path = tmp_path / "hook.sh"
    baseline_path = tmp_path / ".hook.sha256"
    hook_path.write_text("echo 1\n", encoding="utf-8")
    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)

    hook_path.write_text("echo 2\n", encoding="utf-8")

    rc = main(
        [
            "verify-hook",
            "--hook-path",
            str(hook_path),
            "--baseline-path",
            str(baseline_path),
            "--json",
        ]
    )
    assert rc == 1
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["ok"] is False


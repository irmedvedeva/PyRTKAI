from __future__ import annotations

from pathlib import Path

from pyrtkai.integrity import (
    HookIntegrityResult,
    store_sha256_baseline,
    verify_sha256_baseline,
)


def test_verify_sha256_baseline_ok(tmp_path: Path) -> None:
    hook_path = tmp_path / "hook.sh"
    baseline_path = tmp_path / ".hook.sha256"
    hook_path.write_text("echo 1\n", encoding="utf-8")

    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)
    res = verify_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)
    assert isinstance(res, HookIntegrityResult)
    assert res.ok is True


def test_verify_sha256_baseline_tampered(tmp_path: Path) -> None:
    hook_path = tmp_path / "hook.sh"
    baseline_path = tmp_path / ".hook.sha256"
    hook_path.write_text("echo 1\n", encoding="utf-8")
    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)

    hook_path.write_text("echo 2\n", encoding="utf-8")
    res = verify_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)
    assert res.ok is False
    assert res.reason == "tampered"


def test_verify_missing_baseline_is_fail_closed(tmp_path: Path) -> None:
    hook_path = tmp_path / "hook.sh"
    baseline_path = tmp_path / ".hook.sha256"
    hook_path.write_text("echo 1\n", encoding="utf-8")

    res = verify_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)
    assert res.ok is False
    assert res.reason == "missing_or_invalid_baseline"


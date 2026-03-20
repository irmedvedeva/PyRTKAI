from __future__ import annotations

import json
from pathlib import Path

import pytest

from pyrtkai.cli import main
from pyrtkai.cli_doctor import _HOOKS_JSON_MAX_BYTES
from pyrtkai.integrity import store_sha256_baseline

MVP_ENV_VARS = (
    "PYRTKAI_MVP_ENABLE_GIT_STATUS",
    "PYRTKAI_MVP_ENABLE_LS",
    "PYRTKAI_MVP_ENABLE_GREP",
    "PYRTKAI_MVP_ENABLE_RG",
)


def _write_hooks_json(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    hooks_json = {
        "version": 1,
        "hooks": {
            "preToolUse": [
                {"command": "./hooks/pyrtkai-rewrite.sh", "matcher": "Shell"}
            ]
        },
    }
    path.write_text(json.dumps(hooks_json), encoding="utf-8")


def test_doctor_before_shell_execution_resolves_hook_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Doctor follows beforeShellExecution entries to non-default hook locations."""
    monkeypatch.setenv("HOME", str(tmp_path))
    for var in MVP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    home_cursor = tmp_path / ".cursor"
    custom_dir = home_cursor / "plugin-scripts"
    hook_path = custom_dir / "pyrtkai-rewrite.sh"
    baseline_path = custom_dir / ".pyrtkai-rewrite.sh.sha256"
    custom_dir.mkdir(parents=True, exist_ok=True)
    hook_path.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)

    hooks_json = {
        "version": 1,
        "hooks": {
            "beforeShellExecution": [
                {"command": str(hook_path)},
            ]
        },
    }
    (home_cursor / "hooks.json").write_text(json.dumps(hooks_json), encoding="utf-8")

    rc = main(["doctor", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["hooks_json"]["configured"] is True
    assert payload["hook_integrity"]["ok"] is True
    assert payload["hook_integrity"]["hook_path"] == str(hook_path)


def test_doctor_ok(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    for var in MVP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    home_cursor = tmp_path / ".cursor"
    hooks_dir = home_cursor / "hooks"
    hook_path = hooks_dir / "pyrtkai-rewrite.sh"
    baseline_path = hooks_dir / ".pyrtkai-rewrite.sh.sha256"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)

    _write_hooks_json(home_cursor / "hooks.json")

    rc = main(["doctor", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["hook_integrity"]["ok"] is True
    assert payload["hooks_json"]["configured"] is True
    assert payload["mvp_rewrite_rules"] == {
        "git_status": True,
        "ls": True,
        "grep": True,
        "rg": True,
    }


def test_doctor_pre_tool_use_matcher_shell_pipe_form(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    for var in MVP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    home_cursor = tmp_path / ".cursor"
    hooks_dir = home_cursor / "hooks"
    hook_path = hooks_dir / "pyrtkai-rewrite.sh"
    baseline_path = hooks_dir / ".pyrtkai-rewrite.sh.sha256"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)

    hooks_json = {
        "version": 1,
        "hooks": {
            "preToolUse": [
                {
                    "command": "./hooks/pyrtkai-rewrite.sh",
                    "matcher": "Read|Shell",
                }
            ]
        },
    }
    (home_cursor / "hooks.json").write_text(json.dumps(hooks_json), encoding="utf-8")

    rc = main(["doctor", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["hooks_json"]["configured"] is True


def test_doctor_tampered_fails(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    for var in MVP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    home_cursor = tmp_path / ".cursor"
    hooks_dir = home_cursor / "hooks"
    hook_path = hooks_dir / "pyrtkai-rewrite.sh"
    baseline_path = hooks_dir / ".pyrtkai-rewrite.sh.sha256"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)
    hook_path.write_text("#!/usr/bin/env bash\necho tampered\n", encoding="utf-8")

    _write_hooks_json(home_cursor / "hooks.json")

    rc = main(["doctor", "--json"])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["hook_integrity"]["ok"] is False
    assert payload["hooks_json"]["configured"] is True
    assert payload["mvp_rewrite_rules"] == {
        "git_status": True,
        "ls": True,
        "grep": True,
        "rg": True,
    }


def test_doctor_hooks_json_present_but_not_configured(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    for var in MVP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    home_cursor = tmp_path / ".cursor"
    hooks_dir = home_cursor / "hooks"
    hook_path = hooks_dir / "pyrtkai-rewrite.sh"
    baseline_path = hooks_dir / ".pyrtkai-rewrite.sh.sha256"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)

    # hooks.json exists but preToolUse points to a different script name.
    hooks_json = {
        "version": 1,
        "hooks": {
            "preToolUse": [
                {"command": "./hooks/other-rewrite.sh", "matcher": "Shell"}
            ]
        },
    }
    (home_cursor / "hooks.json").write_text(
        json.dumps(hooks_json), encoding="utf-8"
    )

    rc = main(["doctor", "--json"])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["hook_integrity"]["ok"] is True
    assert payload["hooks_json"]["present"] is True
    assert payload["hooks_json"]["configured"] is False
    assert payload["mvp_rewrite_rules"] == {
        "git_status": True,
        "ls": True,
        "grep": True,
        "rg": True,
    }


def test_doctor_hooks_json_exceeds_max_bytes_not_configured(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    for var in MVP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    home_cursor = tmp_path / ".cursor"
    hooks_dir = home_cursor / "hooks"
    hook_path = hooks_dir / "pyrtkai-rewrite.sh"
    baseline_path = hooks_dir / ".pyrtkai-rewrite.sh.sha256"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)

    huge = home_cursor / "hooks.json"
    huge.write_bytes(b"x" * (_HOOKS_JSON_MAX_BYTES + 1))

    rc = main(["doctor", "--json"])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["hook_integrity"]["ok"] is True
    assert payload["hooks_json"]["present"] is True
    assert payload["hooks_json"]["configured"] is False


def test_doctor_mvp_rules_respect_env(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    for var in MVP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("PYRTKAI_MVP_ENABLE_RG", "0")

    home_cursor = tmp_path / ".cursor"
    hooks_dir = home_cursor / "hooks"
    hook_path = hooks_dir / "pyrtkai-rewrite.sh"
    baseline_path = hooks_dir / ".pyrtkai-rewrite.sh.sha256"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    store_sha256_baseline(hook_path=hook_path, baseline_path=baseline_path)

    _write_hooks_json(home_cursor / "hooks.json")

    rc = main(["doctor", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["mvp_rewrite_rules"]["rg"] is False
    assert payload["mvp_rewrite_rules"]["ls"] is True


def test_config_json_default(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for var in MVP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    rc = main(["config", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["mvp_rewrite_rules"] == {
        "git_status": True,
        "ls": True,
        "grep": True,
        "rg": True,
    }


def test_config_json_respects_env(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for var in MVP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("PYRTKAI_MVP_ENABLE_LS", "0")

    rc = main(["config", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["mvp_rewrite_rules"]["ls"] is False


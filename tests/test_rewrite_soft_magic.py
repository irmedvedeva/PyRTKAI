"""P2: suggested_command + --explain on rewrite; argv-safety guardrails."""

from __future__ import annotations

import json
import shlex
import sys

import pytest

from pyrtkai.cli import main


def test_rewrite_skip_without_explain_omits_explain_key(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["rewrite", "echo", "hello"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["action"] == "skip"
    assert "explain" not in payload
    assert payload.get("skip_code") == "unsupported_mvp"
    assert "suggested_command" in payload


def test_rewrite_explain_flag_includes_block(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["rewrite", "--explain", "echo", "hello"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    ex = payload["explain"]
    assert ex["code"] == "unsupported_mvp"
    assert "why" in ex and "remediation" in ex


def test_rewrite_unsupported_suggested_matches_shlex_join(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["rewrite", "echo", "hello"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    expected = shlex.join(
        [sys.executable, "-m", "pyrtkai.cli", "proxy", "echo", "hello"]
    )
    assert payload["suggested_command"] == expected


def test_rewrite_shell_meta_suggested_is_static_example(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["rewrite", "echo", "a", "&&", "echo", "b"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["skip_code"] == "shell_metacharacters"
    sc = payload["suggested_command"]
    assert "print(1)" in sc
    assert "&&" not in sc
    assert "$(echo" not in sc


def test_rewrite_rtk_disabled_suggested_removes_assignment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["rewrite", "RTK_DISABLED=1", "git", "status"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["skip_code"] == "rtk_disabled"
    assert payload["suggested_command"] == "git status"


def test_rewrite_empty_emits_skip_code(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["rewrite"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["action"] == "skip"
    assert payload["skip_code"] == "empty"


def test_rewrite_supported_includes_explicit_disable_env(
    capsys: pytest.CaptureFixture[str],
) -> None:
    cases = [
        (
            ["rewrite", "git", "status"],
            "git_status",
            "export PYRTKAI_MVP_ENABLE_GIT_STATUS=0",
        ),
        (
            ["rewrite", "ls", "-la"],
            "ls",
            "export PYRTKAI_MVP_ENABLE_LS=0",
        ),
        (
            ["rewrite", "grep", "foo", "README.md"],
            "grep",
            "export PYRTKAI_MVP_ENABLE_GREP=0",
        ),
        (
            ["rewrite", "rg", "foo", "src"],
            "rg",
            "export PYRTKAI_MVP_ENABLE_RG=0",
        ),
    ]
    for argv, expected_rule_id, expected_disable in cases:
        rc = main(argv)
        assert rc == 0
        payload = json.loads(capsys.readouterr().out.strip())
        assert payload["action"] == "rewrite"
        assert payload["rewrite_rule_id"] == expected_rule_id
        assert payload["suggested_disable_env"] == expected_disable


def test_rewrite_supported_explain_mentions_disable_env(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["rewrite", "--explain", "git", "status"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    ex = payload["explain"]
    assert ex["code"] == "rewrite_rule_git_status"
    assert "PYRTKAI_MVP_ENABLE_GIT_STATUS=0" in ex["remediation"]


def test_rewrite_git_log_rule_and_disable_hint(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["rewrite", "git", "log", "-n", "1"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["action"] == "rewrite"
    assert payload["rewrite_rule_id"] == "git_log"
    assert payload["suggested_disable_env"] == "export PYRTKAI_MVP_ENABLE_GIT_LOG=0"

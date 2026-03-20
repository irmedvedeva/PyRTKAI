from __future__ import annotations

import pytest

from pyrtkai.policy import evaluate_permission


def test_no_deny_patterns_allows_without_length_check(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)
    monkeypatch.delenv("PYRTKAI_DENY_REGEX", raising=False)
    long_cmd = "x" * 200_000
    d = evaluate_permission(original_command=long_cmd, rewritten_command=None)
    assert d.permission_decision == "allow"


def test_deny_when_original_exceeds_max_input_chars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "git")
    monkeypatch.setenv("PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS", "20")
    long_cmd = "x" * 21
    d = evaluate_permission(original_command=long_cmd, rewritten_command=None)
    assert d.permission_decision == "deny"
    assert "exceeds" in d.reason.lower()
    assert "PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS" in d.reason


def test_deny_when_rewritten_exceeds_max_input_chars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "git")
    monkeypatch.setenv("PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS", "15")
    d = evaluate_permission(
        original_command="git status",
        rewritten_command="y" * 16,
    )
    assert d.permission_decision == "deny"
    assert "exceeds" in d.reason.lower()


def test_under_limit_still_matches_deny_regex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "secret")
    monkeypatch.setenv("PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS", "100")
    d = evaluate_permission(original_command="echo secret", rewritten_command=None)
    assert d.permission_decision == "deny"
    assert "deny pattern matched" in d.reason

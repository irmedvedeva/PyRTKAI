from __future__ import annotations

import json
import sys

import pytest

from tests.harness import run_command


def _call_hook(input_payload: dict[str, object], *, timeout_s: float = 10.0) -> str:
    stdin_json = json.dumps(input_payload)
    result = run_command(
        [sys.executable, "-m", "pyrtkai.cli", "hook"],
        input_text=stdin_json,
        timeout_s=timeout_s,
    )
    assert result.returncode == 0
    return result.stdout


def test_claude_hook_allow_rewrites_git_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)
    monkeypatch.delenv("PYRTKAI_DENY_REGEX", raising=False)

    stdout = _call_hook(
        {"hookEventName": "PreToolUse", "tool_input": {"command": "git status"}}
    )
    payload = json.loads(stdout)

    hook_out = payload["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "allow"
    assert hook_out["updatedInput"]["command"] == "pyrtkai proxy git status"


def test_claude_hook_deny_when_original_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "git status")

    stdout = _call_hook(
        {"hookEventName": "PreToolUse", "tool_input": {"command": "git status"}}
    )
    payload = json.loads(stdout)

    hook_out = payload["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    assert hook_out["updatedInput"]["command"] == "git status"


def test_claude_hook_deny_when_rewritten_only_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Only the rewritten wrapper contains this string.
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "pyrtkai proxy git status")

    stdout = _call_hook(
        {"hookEventName": "PreToolUse", "tool_input": {"command": "git status"}}
    )
    payload = json.loads(stdout)

    hook_out = payload["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    # Fail-closed deny keeps original command.
    assert hook_out["updatedInput"]["command"] == "git status"


def test_cursor_hook_rewrite_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)

    stdout = _call_hook({"tool_input": {"command": "git status"}})
    payload = json.loads(stdout)

    assert payload["permission"] == "allow"
    assert payload["updated_input"]["command"] == "pyrtkai proxy git status"


def test_cursor_hook_rewrite_blocked_by_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "pyrtkai proxy git status")

    stdout = _call_hook({"tool_input": {"command": "git status"}})
    payload = json.loads(stdout)

    assert payload == {}


def test_gemini_hook_rewrite_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)

    stdout = _call_hook(
        {"tool_name": "run_shell_command", "tool_input": {"command": "git status"}}
    )
    payload = json.loads(stdout)

    assert payload["decision"] == "allow"
    assert (
        payload["hookSpecificOutput"]["tool_input"]["command"] == "pyrtkai proxy git status"
    )


def test_gemini_hook_rewrite_blocked_by_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "pyrtkai proxy git status")

    stdout = _call_hook(
        {"tool_name": "run_shell_command", "tool_input": {"command": "git status"}}
    )
    payload = json.loads(stdout)

    assert payload == {"decision": "allow"}


def test_copilot_cli_hook_suggest_rewrite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)

    # Copilot CLI: toolArgs is a JSON-encoded string.
    tool_args = json.dumps({"command": "git status"})
    stdout = _call_hook({"toolName": "bash", "toolArgs": tool_args})
    payload = json.loads(stdout)

    assert payload["permissionDecision"] == "deny"
    assert "pyrtkai proxy git status" in payload["permissionDecisionReason"]


def test_copilot_cli_hook_deny_on_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "git status")

    tool_args = json.dumps({"command": "git status"})
    stdout = _call_hook({"toolName": "bash", "toolArgs": tool_args})
    payload = json.loads(stdout)

    assert payload["permissionDecision"] == "deny"
    assert "deny pattern matched" in payload["permissionDecisionReason"]


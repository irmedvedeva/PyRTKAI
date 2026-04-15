from __future__ import annotations

import json
import shlex
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


def _call_hook_raw(stdin_json: str, *, timeout_s: float = 10.0) -> str:
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
    expected = (
        f"{shlex.quote(sys.executable)} -m pyrtkai.cli proxy git status"
    )
    assert hook_out["updatedInput"]["command"] == expected


def test_claude_hook_deny_when_original_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "git status")

    stdout = _call_hook(
        {"hookEventName": "PreToolUse", "tool_input": {"command": "git status"}}
    )
    payload = json.loads(stdout)

    hook_out = payload["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    assert hook_out["updatedInput"]["command"] == "git status"
    assert hook_out["explain"]["code"] == "policy_regex"


def test_claude_hook_deny_when_rewritten_only_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Only the rewritten wrapper contains this string.
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "pyrtkai.cli proxy git status")

    stdout = _call_hook(
        {"hookEventName": "PreToolUse", "tool_input": {"command": "git status"}}
    )
    payload = json.loads(stdout)

    hook_out = payload["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    # Fail-closed deny keeps original command.
    assert hook_out["updatedInput"]["command"] == "git status"
    assert hook_out["explain"]["code"] == "policy_regex"


def test_cursor_hook_rewrite_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)

    stdout = _call_hook({"tool_input": {"command": "git status"}})
    payload = json.loads(stdout)

    assert payload["permission"] == "allow"
    expected = (
        f"{shlex.quote(sys.executable)} -m pyrtkai.cli proxy git status"
    )
    assert payload["updated_input"]["command"] == expected


def test_cursor_hook_rewrite_blocked_by_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "pyrtkai.cli proxy git status")

    stdout = _call_hook({"tool_input": {"command": "git status"}})
    payload = json.loads(stdout)

    assert payload == {}


def test_cursor_hook_rtk_disabled_opt_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)
    stdout = _call_hook({"tool_input": {"command": "RTK_DISABLED=1 git status"}})
    payload = json.loads(stdout)
    # Fail-safe opt-out: no rewritten command should be suggested.
    assert payload == {}


def test_claude_hook_rtk_disabled_opt_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)
    stdout = _call_hook(
        {"hookEventName": "PreToolUse", "tool_input": {"command": "RTK_DISABLED=1 git status"}}
    )
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
        payload["hookSpecificOutput"]["tool_input"]["command"]
        == f"{shlex.quote(sys.executable)} -m pyrtkai.cli proxy git status"
    )


def test_gemini_hook_rewrite_blocked_by_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "pyrtkai.cli proxy git status")

    stdout = _call_hook(
        {"tool_name": "run_shell_command", "tool_input": {"command": "git status"}}
    )
    payload = json.loads(stdout)

    assert payload == {}


def test_gemini_hook_rtk_disabled_opt_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)
    stdout = _call_hook(
        {"tool_name": "run_shell_command", "tool_input": {"command": "RTK_DISABLED=1 git status"}}
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
    assert "pyrtkai.cli proxy git status" in payload["permissionDecisionReason"]
    assert payload["rewriteRuleHint"]["code"] == "rewrite_rule_git_status"
    assert "PYRTKAI_MVP_ENABLE_GIT_STATUS=0" in payload["rewriteRuleHint"]["remediation"]


def test_copilot_cli_hook_deny_on_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "git status")

    tool_args = json.dumps({"command": "git status"})
    stdout = _call_hook({"toolName": "bash", "toolArgs": tool_args})
    payload = json.loads(stdout)

    assert payload["permissionDecision"] == "deny"
    assert "deny pattern matched" in payload["permissionDecisionReason"]
    assert payload["explain"]["code"] == "policy_regex"
    assert payload["rewriteRuleHint"]["code"] == "rewrite_rule_git_status"


def test_copilot_cli_hook_rtk_disabled_opt_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)
    tool_args = json.dumps({"command": "RTK_DISABLED=1 git status"})
    stdout = _call_hook({"toolName": "bash", "toolArgs": tool_args})
    payload = json.loads(stdout)
    assert payload == {}


def test_hook_malformed_json_is_fail_closed() -> None:
    stdout = _call_hook_raw("{not json")
    payload = json.loads(stdout)
    hook_out = payload["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    assert "invalid hook input JSON" in hook_out["permissionDecisionReason"]
    assert hook_out["explain"]["code"] == "hook_invalid_json"


def test_hook_non_object_json_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)
    stdout = _call_hook_raw('["list instead of object"]')
    payload = json.loads(stdout)
    hook_out = payload["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    assert "hook payload is not an object" in hook_out["permissionDecisionReason"]
    assert hook_out["explain"]["code"] == "hook_payload_not_object"


def test_hook_input_too_large_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYRTKAI_HOOK_MAX_STDIN_BYTES", "32")
    oversized = '{"tool_input":{"command":"' + ("x" * 80) + '"}}'
    stdout = _call_hook_raw(oversized)
    payload = json.loads(stdout)
    hook_out = payload["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    assert "PYRTKAI_HOOK_MAX_STDIN_BYTES" in hook_out["permissionDecisionReason"]
    assert hook_out["explain"]["code"] == "hook_input_too_large"


def test_hook_unknown_schema_without_command_is_safe_pass_through() -> None:
    stdout = _call_hook_raw('{"unexpected": "shape"}')
    payload = json.loads(stdout)
    assert payload == {}


def test_hook_invalid_deny_regex_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    # Invalid regex config must deny rather than crash or allow.
    monkeypatch.setenv("PYRTKAI_DENY_REGEXES", "(*invalid-regex")
    stdout = _call_hook(
        {"hookEventName": "PreToolUse", "tool_input": {"command": "git status"}}
    )
    payload = json.loads(stdout)
    hook_out = payload["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    assert "policy config error" in hook_out["permissionDecisionReason"]
    assert hook_out["updatedInput"]["command"] == "git status"
    assert hook_out["explain"]["code"] == "policy_config"


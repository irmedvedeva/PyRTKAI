from __future__ import annotations

import json
from dataclasses import dataclass

from pyrtkai.contracts import RewriteDecision
from pyrtkai.policy import evaluate_permission
from pyrtkai.rewriter import get_default_rewriter
from pyrtkai.shell_parse import extract_env_prefix


@dataclass(frozen=True)
class HookOutputClaude:
    permission_decision: str  # "allow" | "deny"
    permission_decision_reason: str
    updated_command: str

    def to_dict(self) -> dict[str, object]:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": self.permission_decision,
                "permissionDecisionReason": self.permission_decision_reason,
                "updatedInput": {"command": self.updated_command},
            }
        }


def _try_get_tool_input_command(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        cmd = tool_input.get("command")
        if isinstance(cmd, str) and cmd.strip():
            return cmd.strip()
    return None


def _try_get_tool_input_command_snake(payload: object) -> str | None:
    # VS Code/Claude: usually snake_case tool_input.command.
    return _try_get_tool_input_command(payload)


def _try_get_copilot_cli_command(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    if payload.get("toolName") != "bash":
        return None
    tool_args_str = payload.get("toolArgs")
    if not isinstance(tool_args_str, str) or not tool_args_str.strip():
        return None
    try:
        tool_args = json.loads(tool_args_str)
    except json.JSONDecodeError:
        return None
    if not isinstance(tool_args, dict):
        return None
    cmd = tool_args.get("command")
    if isinstance(cmd, str) and cmd.strip():
        return cmd.strip()
    return None


def _detect_hook_kind(payload: dict[str, object]) -> str:
    # Copilot CLI: camelCase toolName/toolArgs.
    if payload.get("toolName") == "bash":
        return "copilot_cli"
    # Gemini CLI: tool_name == run_shell_command.
    if payload.get("tool_name") == "run_shell_command":
        return "gemini"
    # Cursor agent: tool_input.command without tool_name, and without hookEventName.
    if "tool_name" not in payload and "hookEventName" not in payload:
        return "cursor"
    # Fallback: Claude/VSCodes-like.
    return "claude"


def _rewrite_and_policy(original_cmd: str) -> tuple[RewriteDecision, str | None]:
    env_prefix, cmd_wo_prefix = extract_env_prefix(original_cmd)
    rewriter = get_default_rewriter()
    rewrite_decision = rewriter.rewrite(cmd_wo_prefix, env_prefix)
    rewritten_cmd = (
        rewrite_decision.rewritten_cmd if rewrite_decision.action == "rewrite" else None
    )
    return rewrite_decision, rewritten_cmd


def handle_hook_json(stdin_json: str) -> dict[str, object]:
    """
    Handle multiple agent hook schemas.

    Output behavior (fail-closed):
    - If deny matches: return a provider-specific deny response where possible.
    - If deny/rewrite is not possible: pass through (return `{}`) so we never rewrite.
    """
    try:
        payload_obj = json.loads(stdin_json)
    except json.JSONDecodeError:
        # Can't parse: fail-closed by returning deny.
        # (Do not rely on evaluate_permission() because no deny-regexes may be configured.)
        return HookOutputClaude(
            permission_decision="deny",
            permission_decision_reason="invalid hook input JSON (fail-closed)",
            updated_command="",
        ).to_dict()

    if not isinstance(payload_obj, dict):
        return HookOutputClaude(
            permission_decision="deny",
            permission_decision_reason="hook payload is not an object (fail-closed)",
            updated_command="",
        ).to_dict()

    payload = payload_obj
    kind = _detect_hook_kind(payload)

    if kind in {"cursor", "gemini", "claude"}:
        original_cmd = _try_get_tool_input_command_snake(payload)
    elif kind == "copilot_cli":
        original_cmd = _try_get_copilot_cli_command(payload)
    else:
        original_cmd = None

    if not original_cmd:
        # Missing command: pass-through (no rewrite).
        return {}

    rewrite_decision, rewritten_cmd = _rewrite_and_policy(original_cmd)

    policy = evaluate_permission(
        original_command=original_cmd,
        rewritten_command=rewritten_cmd,
    )

    # Provider-specific output formats.
    if kind == "cursor":
        # Cursor hook format expects: {"permission":"allow","updated_input":{...}}
        if policy.permission_decision == "allow" and rewrite_decision.action == "rewrite":
            return {
                "permission": "allow",
                "updated_input": {"command": rewritten_cmd},
            }
        return {}

    if kind == "gemini":
        # Gemini CLI: decision allow + optional hookSpecificOutput.tool_input.command.
        if policy.permission_decision == "allow" and rewrite_decision.action == "rewrite":
            return {
                "decision": "allow",
                "hookSpecificOutput": {
                    "tool_input": {"command": rewritten_cmd}
                },
            }
        return {"decision": "allow"}

    if kind == "copilot_cli":
        # Copilot CLI RTK approach: output permissionDecision=deny with a token-savings reason.
        if policy.permission_decision == "deny":
            # For fail-closed rewrite, we deny here (no suggestion rewrite).
            return {
                "permissionDecision": "deny",
                "permissionDecisionReason": policy.reason,
            }
        if rewrite_decision.action == "rewrite":
            return {
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Token savings: use "
                    f"`{rewritten_cmd}` instead (rtk saves 60-90% tokens)"
                ),
            }
        return {}

    # Claude/VSCodes-like output with permissionDecision + updatedInput.
    if policy.permission_decision == "deny":
        return HookOutputClaude(
            permission_decision="deny",
            permission_decision_reason=policy.reason,
            updated_command=original_cmd,
        ).to_dict()

    if policy.permission_decision == "allow" and rewrite_decision.action == "rewrite":
        return HookOutputClaude(
            permission_decision="allow",
            permission_decision_reason=policy.reason,
            updated_command=rewritten_cmd or original_cmd,
        ).to_dict()

    return {}


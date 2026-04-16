from __future__ import annotations

import shlex
import sys
from typing import Final

# Stable machine ids for skip/remediation (CLI JSON / tests).
SKIP_RTK_DISABLED: Final = "rtk_disabled"
SKIP_HEREDOC: Final = "heredoc"
SKIP_SHELL_METACHAR: Final = "shell_metacharacters"
SKIP_EMPTY: Final = "empty"
SKIP_UNSUPPORTED_MVP: Final = "unsupported_mvp"
SKIP_UNBALANCED_QUOTES: Final = "unbalanced_quotes"

EXPLAIN_SKIP: dict[str, dict[str, str]] = {
    SKIP_RTK_DISABLED: {
        "code": SKIP_RTK_DISABLED,
        "why": "Rewrite is skipped when RTK_DISABLED appears in leading environment assignments.",
        "remediation": "Remove RTK_DISABLED=... from the prefix, then run rewrite again.",
    },
    SKIP_HEREDOC: {
        "code": SKIP_HEREDOC,
        "why": "Heredoc (<<) is not rewritten; execution would require a shell.",
        "remediation": "Use a file, pipe, or argv-safe command instead of a heredoc.",
    },
    SKIP_SHELL_METACHAR: {
        "code": SKIP_SHELL_METACHAR,
        "why": "Compound operators, pipes, redirects, or background markers were detected.",
        "remediation": (
            "Run one argv-safe program via pyrtkai proxy (no &&, |, ;, redirects). "
            "See suggested_command for a minimal example."
        ),
    },
    SKIP_EMPTY: {
        "code": SKIP_EMPTY,
        "why": "There is no command to rewrite.",
        "remediation": "Pass a non-empty command to pyrtkai rewrite.",
    },
    SKIP_UNSUPPORTED_MVP: {
        "code": SKIP_UNSUPPORTED_MVP,
        "why": (
            "This command is not in the MVP rewrite registry "
            "(git status, git log, ls, grep, rg)."
        ),
        "remediation": (
            "Call pyrtkai proxy yourself for output filtering, or use a supported command shape."
        ),
    },
    SKIP_UNBALANCED_QUOTES: {
        "code": SKIP_UNBALANCED_QUOTES,
        "why": "Quotes appear unbalanced; rewrite refuses to parse the string.",
        "remediation": "Fix quoting, then retry rewrite.",
    },
}

EXPLAIN_POLICY: dict[str, dict[str, str]] = {
    "policy_config": {
        "code": "policy_config",
        "why": "Deny-regex configuration could not be loaded.",
        "remediation": (
            "Fix PYRTKAI_DENY_REGEXES / PYRTKAI_DENY_REGEX patterns (valid Python regex)."
        ),
    },
    "policy_length": {
        "code": "policy_length",
        "why": "The command exceeded PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS before regex matching.",
        "remediation": (
            "Shorten the command or raise PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS (careful: cost)."
        ),
    },
    "policy_regex": {
        "code": "policy_regex",
        "why": "A configured deny regex matched the original or rewritten command.",
        "remediation": "Narrow PYRTKAI_DENY_REGEXES or adjust the command so it is allowed.",
    },
}


def strip_rtk_disabled_assignments(env_prefix: str) -> str:
    toks = [t for t in env_prefix.split() if not t.startswith("RTK_DISABLED=")]
    return " ".join(toks).strip()


def suggested_command_after_rtk_disabled(*, env_prefix: str, cmd_wo_prefix: str) -> str:
    new_prefix = strip_rtk_disabled_assignments(env_prefix)
    parts = [p for p in (new_prefix, cmd_wo_prefix.strip()) if p]
    return " ".join(parts)


def suggested_proxy_argv_for_tokens(argv_tail: list[str]) -> str:
    """
    Argv-safe string for copy-paste: quoted tokens, no shell=True.
    """
    head = [sys.executable, "-m", "pyrtkai.cli", "proxy", *argv_tail]
    return shlex.join(head)


def static_proxy_example_command() -> str:
    """Minimal example without user-controlled fragments."""
    return shlex.join(
        [sys.executable, "-m", "pyrtkai.cli", "proxy", "--", "python3", "-c", "print(1)"]
    )


def explain_skip(skip_code: str) -> dict[str, str]:
    return dict(EXPLAIN_SKIP[skip_code])


def explain_rewrite_rule_disable(*, rule_id: str, disable_export: str) -> dict[str, str]:
    return {
        "code": f"rewrite_rule_{rule_id}",
        "why": "This command matched an enabled MVP rewrite rule.",
        "remediation": (
            "If you want raw command execution for this class, disable the rule explicitly: "
            f"`{disable_export}`."
        ),
    }


def rewrite_rule_disable_hint(
    *, rule_id: str | None, disable_export: str | None
) -> dict[str, str] | None:
    if not rule_id or not disable_export:
        return None
    return explain_rewrite_rule_disable(rule_id=rule_id, disable_export=disable_export)


def explain_policy(policy_code: str) -> dict[str, str]:
    return dict(EXPLAIN_POLICY[policy_code])


EXPLAIN_HOOK: dict[str, dict[str, str]] = {
    "hook_invalid_json": {
        "code": "hook_invalid_json",
        "why": "Hook stdin was not valid JSON (fail-closed deny).",
        "remediation": "Ensure the agent sends a JSON object with the expected tool fields.",
    },
    "hook_payload_not_object": {
        "code": "hook_payload_not_object",
        "why": "Hook JSON root was not an object (fail-closed deny).",
        "remediation": "Send a JSON object payload for the hook.",
    },
    "hook_input_too_large": {
        "code": "hook_input_too_large",
        "why": "Hook stdin exceeded the configured byte cap and was denied.",
        "remediation": (
            "Reduce hook payload size or increase PYRTKAI_HOOK_MAX_STDIN_BYTES "
            "in trusted environments."
        ),
    },
}


def explain_hook(code: str) -> dict[str, str]:
    return dict(EXPLAIN_HOOK[code])

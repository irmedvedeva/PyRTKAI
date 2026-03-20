from __future__ import annotations

import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    permission_decision: str  # "allow" | "deny"
    reason: str
    final_command: str


def _load_deny_patterns_from_env() -> tuple[list[re.Pattern[str]], str | None]:
    """
    Load deny regexes from env.

    Env:
      - PYRTKAI_DENY_REGEXES: comma-separated regex patterns
      - PYRTKAI_DENY_REGEX: single regex

    Fail-closed behavior: if config parsing fails, return ([], error_message).
    """
    deny_raw = os.environ.get("PYRTKAI_DENY_REGEXES")
    deny_single = os.environ.get("PYRTKAI_DENY_REGEX")
    parts: list[str] = []
    if deny_raw:
        parts = [p.strip() for p in deny_raw.split(",") if p.strip()]
    elif deny_single:
        parts = [deny_single.strip()] if deny_single.strip() else []

    if not parts:
        return ([], None)

    patterns: list[re.Pattern[str]] = []
    for p in parts:
        try:
            patterns.append(re.compile(p))
        except re.error as e:
            return ([], f"invalid deny regex: {p!r} ({e})")
    return patterns, None


def _load_max_deny_input_chars() -> int:
    """
    Cap command length before applying deny regexes (mitigates pathological regex cost).

    Env: PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS (default 65536). Invalid/ non-positive → default.
    """
    raw = os.environ.get("PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS", "65536").strip()
    try:
        n = int(raw)
        return n if n > 0 else 65536
    except ValueError:
        return 65536


def evaluate_permission(
    *,
    original_command: str,
    rewritten_command: str | None,
) -> PolicyDecision:
    patterns, config_error = _load_deny_patterns_from_env()
    if config_error is not None:
        return PolicyDecision(
            permission_decision="deny",
            reason=f"policy config error (fail-closed): {config_error}",
            final_command=original_command,
        )

    if not patterns:
        final = rewritten_command if rewritten_command is not None else original_command
        return PolicyDecision(
            permission_decision="allow",
            reason="no deny patterns matched",
            final_command=final,
        )

    max_chars = _load_max_deny_input_chars()
    candidates = [original_command]
    if rewritten_command:
        candidates.append(rewritten_command)

    for cand in candidates:
        if len(cand) > max_chars:
            return PolicyDecision(
                permission_decision="deny",
                reason=(
                    f"command length {len(cand)} exceeds "
                    f"PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS ({max_chars}) (fail-closed)"
                ),
                final_command=original_command,
            )

    for cand in candidates:
        for pat in patterns:
            if pat.search(cand):
                return PolicyDecision(
                    permission_decision="deny",
                    reason=f"deny pattern matched: {pat.pattern!r}",
                    final_command=original_command,
                )

    final = rewritten_command if rewritten_command is not None else original_command
    return PolicyDecision(
        permission_decision="allow",
        reason="no deny patterns matched",
        final_command=final,
    )


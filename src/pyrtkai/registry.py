from __future__ import annotations

import os
import shlex
import sys
from dataclasses import dataclass

from pyrtkai.contracts import RewriteDecision
from pyrtkai.rewrite_hints import (
    SKIP_EMPTY,
    SKIP_UNSUPPORTED_MVP,
    suggested_proxy_argv_for_tokens,
)
from pyrtkai.shell_parse import tokenize_shell_like


@dataclass(frozen=True)
class RewriteRule:
    rule_id: str
    base_tokens: tuple[str, ...]
    env_toggle: str

    def matches(self, tokens: list[str]) -> bool:
        if not tokens:
            return False
        if len(tokens) < len(self.base_tokens):
            return False
        return tuple(tokens[: len(self.base_tokens)]) == self.base_tokens

    def disable_export_command(self) -> str:
        return f"export {self.env_toggle}=0"


def _already_wrapped(tokens: list[str]) -> bool:
    # Conservative: if command already starts with our wrapper, do not rewrite again.
    return bool(tokens) and tokens[0] in {"pyrtkai", "rtk"}


def _env_enabled(name: str, *, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"0", "false", "no", "off"}:
        return False
    if normalized in {"1", "true", "yes", "on"}:
        return True
    return default


def get_mvp_rewrite_rules_enabled() -> dict[str, bool]:
    return {
        "git_status": _env_enabled("PYRTKAI_MVP_ENABLE_GIT_STATUS", default=True),
        "git_log": _env_enabled("PYRTKAI_MVP_ENABLE_GIT_LOG", default=True),
        "ls": _env_enabled("PYRTKAI_MVP_ENABLE_LS", default=True),
        "grep": _env_enabled("PYRTKAI_MVP_ENABLE_GREP", default=True),
        "rg": _env_enabled("PYRTKAI_MVP_ENABLE_RG", default=True),
    }


def _match_supported_rule_for_mvp(cmd_wo_prefix: str) -> RewriteRule | None:
    tokens = tokenize_shell_like(cmd_wo_prefix)
    if _already_wrapped(tokens):
        return None

    # Structured/templated output is harder to safely compress in MVP.
    lowered = cmd_wo_prefix.lower()
    if "--json" in lowered or "--template" in lowered or "--format" in lowered:
        return None

    enabled = get_mvp_rewrite_rules_enabled()
    rules: list[RewriteRule] = []
    if enabled.get("git_status"):
        rules.append(
            RewriteRule(
                rule_id="git_status",
                base_tokens=("git", "status"),
                env_toggle="PYRTKAI_MVP_ENABLE_GIT_STATUS",
            )
        )
    if enabled.get("git_log"):
        rules.append(
            RewriteRule(
                rule_id="git_log",
                base_tokens=("git", "log"),
                env_toggle="PYRTKAI_MVP_ENABLE_GIT_LOG",
            )
        )
    if enabled.get("ls"):
        rules.append(
            RewriteRule(
                rule_id="ls",
                base_tokens=("ls",),
                env_toggle="PYRTKAI_MVP_ENABLE_LS",
            )
        )
    if enabled.get("grep"):
        rules.append(
            RewriteRule(
                rule_id="grep",
                base_tokens=("grep",),
                env_toggle="PYRTKAI_MVP_ENABLE_GREP",
            )
        )
    if enabled.get("rg"):
        rules.append(
            RewriteRule(
                rule_id="rg",
                base_tokens=("rg",),
                env_toggle="PYRTKAI_MVP_ENABLE_RG",
            )
        )

    for rule in rules:
        if rule.matches(tokens):
            return rule
    return None


def is_supported_for_mvp(cmd_wo_prefix: str) -> bool:
    return _match_supported_rule_for_mvp(cmd_wo_prefix) is not None


def rewrite_to_proxy(cmd_wo_prefix: str) -> str:
    # For MVP: "rewrite" becomes "wrap with proxy". Real compression mapping comes later.
    py = shlex.quote(sys.executable)
    # Use absolute python invocation so the agent can execute the proxy even if `pyrtkai`
    # is not on PATH in the hook/tool runner environment.
    return f"{py} -m pyrtkai.cli proxy {cmd_wo_prefix}".strip()


def default_registry_rewrite(cmd_wo_prefix: str) -> RewriteDecision:
    if not cmd_wo_prefix.strip():
        return RewriteDecision(
            action="skip",
            reason="empty command",
            skip_code=SKIP_EMPTY,
        )

    matched_rule = _match_supported_rule_for_mvp(cmd_wo_prefix)
    if matched_rule is None:
        tokens = tokenize_shell_like(cmd_wo_prefix)
        suggested = suggested_proxy_argv_for_tokens(tokens) if tokens else None
        return RewriteDecision(
            action="skip",
            reason="unsupported command for MVP rewrite",
            skip_code=SKIP_UNSUPPORTED_MVP,
            suggested_command=suggested,
        )

    return RewriteDecision(
        action="rewrite",
        rewritten_cmd=rewrite_to_proxy(cmd_wo_prefix),
        reason="MVP supported command rewrite",
        rewrite_rule_id=matched_rule.rule_id,
        suggested_disable_env=matched_rule.disable_export_command(),
    )


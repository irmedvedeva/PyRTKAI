from __future__ import annotations

import os
import shlex
import sys
from dataclasses import dataclass

from pyrtkai.contracts import RewriteDecision
from pyrtkai.shell_parse import tokenize_shell_like


@dataclass(frozen=True)
class RewriteRule:
    base_tokens: tuple[str, ...]

    def matches(self, tokens: list[str]) -> bool:
        if not tokens:
            return False
        if len(tokens) < len(self.base_tokens):
            return False
        return tuple(tokens[: len(self.base_tokens)]) == self.base_tokens


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
        "ls": _env_enabled("PYRTKAI_MVP_ENABLE_LS", default=True),
        "grep": _env_enabled("PYRTKAI_MVP_ENABLE_GREP", default=True),
        "rg": _env_enabled("PYRTKAI_MVP_ENABLE_RG", default=True),
    }


def is_supported_for_mvp(cmd_wo_prefix: str) -> bool:
    tokens = tokenize_shell_like(cmd_wo_prefix)
    if _already_wrapped(tokens):
        return False

    # Structured/templated output is harder to safely compress in MVP.
    lowered = cmd_wo_prefix.lower()
    if "--json" in lowered or "--template" in lowered or "--format" in lowered:
        return False

    enabled = get_mvp_rewrite_rules_enabled()
    rules: list[RewriteRule] = []
    if enabled.get("git_status"):
        rules.append(RewriteRule(base_tokens=("git", "status")))
    if enabled.get("ls"):
        rules.append(RewriteRule(base_tokens=("ls",)))
    if enabled.get("grep"):
        rules.append(RewriteRule(base_tokens=("grep",)))
    if enabled.get("rg"):
        rules.append(RewriteRule(base_tokens=("rg",)))

    return any(rule.matches(tokens) for rule in rules)


def rewrite_to_proxy(cmd_wo_prefix: str) -> str:
    # For MVP: "rewrite" becomes "wrap with proxy". Real compression mapping comes later.
    py = shlex.quote(sys.executable)
    # Use absolute python invocation so the agent can execute the proxy even if `pyrtkai`
    # is not on PATH in the hook/tool runner environment.
    return f"{py} -m pyrtkai.cli proxy {cmd_wo_prefix}".strip()


def default_registry_rewrite(cmd_wo_prefix: str) -> RewriteDecision:
    if not cmd_wo_prefix.strip():
        return RewriteDecision(action="skip", reason="empty command")

    if not is_supported_for_mvp(cmd_wo_prefix):
        return RewriteDecision(action="skip", reason="unsupported command for MVP rewrite")

    return RewriteDecision(
        action="rewrite",
        rewritten_cmd=rewrite_to_proxy(cmd_wo_prefix),
        reason="MVP supported command rewrite",
    )


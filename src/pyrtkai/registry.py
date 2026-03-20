from __future__ import annotations

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


def is_supported_for_mvp(cmd_wo_prefix: str) -> bool:
    tokens = tokenize_shell_like(cmd_wo_prefix)
    if _already_wrapped(tokens):
        return False

    # Structured/templated output is harder to safely compress in MVP.
    lowered = cmd_wo_prefix.lower()
    if "--json" in lowered or "--template" in lowered or "--format" in lowered:
        return False

    rules = [
        RewriteRule(base_tokens=("git", "status")),
        RewriteRule(base_tokens=("ls",)),
        RewriteRule(base_tokens=("grep",)),
        RewriteRule(base_tokens=("rg",)),
    ]
    return any(rule.matches(tokens) for rule in rules)


def rewrite_to_proxy(cmd_wo_prefix: str) -> str:
    # For MVP: "rewrite" becomes "wrap with proxy". Real compression mapping comes later.
    return f"pyrtkai proxy {cmd_wo_prefix}".strip()


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


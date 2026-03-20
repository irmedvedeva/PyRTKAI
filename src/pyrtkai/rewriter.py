from __future__ import annotations

from dataclasses import dataclass

from pyrtkai.contracts import CommandRewriter, RewriteDecision
from pyrtkai.registry import default_registry_rewrite
from pyrtkai.shell_parse import (
    find_heredoc_marker_outside_quotes,
    has_shell_metacharacters_outside_quotes,
)


def _env_prefix_has_rtk_disabled(env_prefix: str) -> bool:
    """
    True if a leading env token sets RTK_DISABLED (NAME=VALUE), not a substring false positive
    (e.g. SORTK_DISABLED=1 must not match).
    """
    if not env_prefix.strip():
        return False
    for tok in env_prefix.split():
        if tok.startswith("RTK_DISABLED="):
            return True
    return False


@dataclass(frozen=True)
class DefaultCommandRewriter:
    """
    Phase 2 MVP: only decide whether rewrite is allowed (skip vs rewrite).
    Actual rewrite mapping happens in Phase 3 (rule registry).
    """

    def rewrite(self, cmd: str, env_prefix: str) -> RewriteDecision:
        # Gate: RTK_DISABLED in env-prefix means skip rewrite entirely.
        if _env_prefix_has_rtk_disabled(env_prefix):
            return RewriteDecision(action="skip", reason="RTK_DISABLED present in env-prefix")

        if find_heredoc_marker_outside_quotes(cmd):
            return RewriteDecision(
                action="skip",
                reason="heredoc marker detected (conservative skip)",
            )

        if has_shell_metacharacters_outside_quotes(cmd):
            return RewriteDecision(
                action="skip",
                reason="shell metacharacters detected (MVP proxy requires no-shell execution)",
            )

        # Phase 3: apply registry mapping (or skip if unsupported).
        return default_registry_rewrite(cmd)


def get_default_rewriter() -> CommandRewriter:
    return DefaultCommandRewriter()


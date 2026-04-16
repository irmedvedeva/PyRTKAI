from __future__ import annotations

import json
from argparse import Namespace

from pyrtkai.rewrite_hints import (
    SKIP_EMPTY,
    SKIP_UNBALANCED_QUOTES,
    explain_rewrite_rule_disable,
    explain_skip,
)
from pyrtkai.rewriter import get_default_rewriter
from pyrtkai.shell_parse import extract_env_prefix, has_unbalanced_quotes


def run_rewrite(args: Namespace) -> int:
    want_explain = bool(getattr(args, "explain", False))
    command_str = " ".join(args.command_str).strip()
    if not command_str:
        payload: dict[str, object] = {
            "action": "skip",
            "reason": "empty command",
            "skip_code": SKIP_EMPTY,
        }
        if want_explain:
            payload["explain"] = explain_skip(SKIP_EMPTY)
        print(json.dumps(payload))
        return 0

    if has_unbalanced_quotes(command_str):
        payload = {
            "action": "skip",
            "reason": "unbalanced quotes",
            "skip_code": SKIP_UNBALANCED_QUOTES,
        }
        if want_explain:
            payload["explain"] = explain_skip(SKIP_UNBALANCED_QUOTES)
        print(json.dumps(payload))
        return 0

    env_prefix, cmd_wo_prefix = extract_env_prefix(command_str)
    rewriter = get_default_rewriter()
    decision = rewriter.rewrite(cmd_wo_prefix, env_prefix)
    rewrite_payload: dict[str, object] = {
        "action": decision.action,
        "reason": decision.reason,
    }
    if decision.rewritten_cmd is not None:
        rewrite_payload["rewritten_cmd"] = decision.rewritten_cmd
    if decision.skip_code:
        rewrite_payload["skip_code"] = decision.skip_code
    if decision.suggested_command:
        rewrite_payload["suggested_command"] = decision.suggested_command
    if decision.rewrite_rule_id:
        rewrite_payload["rewrite_rule_id"] = decision.rewrite_rule_id
    if decision.suggested_disable_env:
        rewrite_payload["suggested_disable_env"] = decision.suggested_disable_env
    if want_explain and decision.skip_code:
        rewrite_payload["explain"] = explain_skip(decision.skip_code)
    elif (
        want_explain
        and decision.action == "rewrite"
        and decision.rewrite_rule_id
        and decision.suggested_disable_env
    ):
        rewrite_payload["explain"] = explain_rewrite_rule_disable(
            rule_id=decision.rewrite_rule_id,
            disable_export=decision.suggested_disable_env,
        )
    print(json.dumps(rewrite_payload))
    return 0

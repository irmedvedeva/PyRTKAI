from __future__ import annotations

import json
from argparse import Namespace

from pyrtkai.rewriter import get_default_rewriter
from pyrtkai.shell_parse import extract_env_prefix, has_unbalanced_quotes


def run_rewrite(args: Namespace) -> int:
    command_str = " ".join(args.command_str).strip()
    if not command_str:
        print(json.dumps({"action": "skip", "reason": "empty command"}))
        return 0

    if has_unbalanced_quotes(command_str):
        print(json.dumps({"action": "skip", "reason": "unbalanced quotes"}))
        return 0

    env_prefix, cmd_wo_prefix = extract_env_prefix(command_str)
    rewriter = get_default_rewriter()
    decision = rewriter.rewrite(cmd_wo_prefix, env_prefix)
    rewrite_payload: dict[str, str | None] = {
        "action": decision.action,
        "reason": decision.reason,
    }
    if decision.rewritten_cmd is not None:
        rewrite_payload["rewritten_cmd"] = decision.rewritten_cmd
    print(json.dumps(rewrite_payload))
    return 0

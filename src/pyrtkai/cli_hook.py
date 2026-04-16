from __future__ import annotations

import json
import os
import sys

from pyrtkai.hook import HookOutputClaude, explain_hook, handle_hook_json


def _load_hook_max_stdin_bytes() -> int:
    raw = os.environ.get("PYRTKAI_HOOK_MAX_STDIN_BYTES", "1048576").strip()
    try:
        n = int(raw)
        return n if n > 0 else 1048576
    except ValueError:
        return 1048576


def run_hook() -> int:
    max_bytes = _load_hook_max_stdin_bytes()
    # Bound hook stdin to avoid untrusted host payload memory spikes.
    raw = sys.stdin.buffer.read(max_bytes + 1)
    if len(raw) > max_bytes:
        deny = HookOutputClaude(
            permission_decision="deny",
            permission_decision_reason=(
                f"hook input exceeds PYRTKAI_HOOK_MAX_STDIN_BYTES ({max_bytes}) "
                "(fail-closed)"
            ),
            updated_command="",
            explain=explain_hook("hook_input_too_large"),
        ).to_dict()
        print(json.dumps(deny))
        return 0

    stdin_json = raw.decode("utf-8", errors="replace")
    hook_output = handle_hook_json(stdin_json)
    print(json.dumps(hook_output))
    return 0

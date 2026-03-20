from __future__ import annotations

import json
import sys

from pyrtkai.hook import handle_hook_json


def run_hook() -> int:
    stdin_json = sys.stdin.read()
    hook_output = handle_hook_json(stdin_json)
    print(json.dumps(hook_output))
    return 0

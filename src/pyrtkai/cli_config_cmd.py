from __future__ import annotations

import json
from argparse import Namespace
from typing import cast

from pyrtkai.registry import get_mvp_rewrite_rules_enabled


def run_config(args: Namespace) -> int:
    config_payload: dict[str, object] = {
        "mvp_rewrite_rules": get_mvp_rewrite_rules_enabled(),
    }
    if args.json:
        print(json.dumps(config_payload, ensure_ascii=False))
    else:
        mvp = cast(dict[str, bool], config_payload["mvp_rewrite_rules"])
        for name, enabled in mvp.items():
            print(f"{name}={enabled}")
    return 0

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from pyrtkai.integrity import verify_sha256_baseline


def run_verify_hook(args: Namespace) -> int:
    default_hook_path = Path.home() / ".cursor" / "hooks" / "pyrtkai-rewrite.sh"
    default_baseline_path = Path.home() / ".cursor" / "hooks" / ".pyrtkai-rewrite.sh.sha256"

    hook_path = (
        Path(args.hook_path).expanduser()
        if str(args.hook_path).strip()
        else default_hook_path
    )
    baseline_path = (
        Path(args.baseline_path).expanduser()
        if str(args.baseline_path).strip()
        else default_baseline_path
    )

    res = verify_sha256_baseline(
        hook_path=hook_path,
        baseline_path=baseline_path,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "ok": res.ok,
                    "expected": res.expected,
                    "actual": res.actual,
                    "reason": res.reason,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(f"ok={res.ok} reason={res.reason}")
    return 0 if res.ok else 1

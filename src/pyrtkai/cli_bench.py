from __future__ import annotations

import json
import subprocess  # nosec
import sys
import time
from argparse import Namespace
from statistics import mean


def run_bench_proxy(args: Namespace) -> int:
    iters = int(args.iters)
    if iters <= 0:
        iters = 1

    cmd_argv: list[str] = list(args.command)
    if not cmd_argv:
        return 2

    direct_ms: list[float] = []
    proxy_ms: list[float] = []
    direct_rc = 0
    proxy_rc = 0

    for _ in range(iters):
        start = time.perf_counter()
        proc_direct = subprocess.run(  # nosec
            cmd_argv,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        direct_rc = proc_direct.returncode
        direct_ms.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        proc_proxy = subprocess.run(  # nosec
            [sys.executable, "-m", "pyrtkai.cli", "proxy", *cmd_argv],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        proxy_rc = proc_proxy.returncode
        proxy_ms.append((time.perf_counter() - start) * 1000)

    direct_avg = mean(direct_ms)
    proxy_avg = mean(proxy_ms)
    ratio = (proxy_avg / direct_avg) if direct_avg > 0 else None

    result: dict[str, object] = {
        "iters": iters,
        "direct_avg_ms": direct_avg,
        "proxy_avg_ms": proxy_avg,
        "ratio_proxy_to_direct": ratio,
        "direct_exit_code": direct_rc,
        "proxy_exit_code": proxy_rc,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result)

    return 0 if direct_rc == 0 and proxy_rc == 0 else 1

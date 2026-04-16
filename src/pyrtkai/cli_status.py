"""One-screen summary: version, Cursor hook health, optional gain aggregates."""

from __future__ import annotations

import json
import sys
from argparse import Namespace

from pyrtkai import __version__
from pyrtkai.cli_doctor import collect_doctor_report, doctor_payload_ok
from pyrtkai.cli_utils import sanitize_sqlite_limit
from pyrtkai.schema_meta import SCHEMA_STATUS, build_schema_meta
from pyrtkai.tracking import (
    connect,
    load_gain_config,
    summarize_proxy_events_json,
)


def run_status(args: Namespace) -> int:
    doc = collect_doctor_report()
    gain_cfg = load_gain_config()
    limit = sanitize_sqlite_limit(args.limit)
    aggregate: object = None
    if gain_cfg.enabled:
        conn = connect(gain_cfg.db_path)
        try:
            aggregate = json.loads(summarize_proxy_events_json(conn, limit=limit))
        finally:
            conn.close()

    payload: dict[str, object] = {
        "_meta": build_schema_meta(SCHEMA_STATUS),
        "pyrtkai_version": __version__,
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "cursor_ok": doctor_payload_ok(doc),
        "doctor": doc,
        "gain": {
            "enabled": gain_cfg.enabled,
            "db_path": str(gain_cfg.db_path),
            "aggregate": aggregate,
        },
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    print("PyRTKAI status")
    print("==============")
    print(f"pyrtkai {__version__}  |  Python {sys.version.split()[0]}")
    hi = doc.get("hook_integrity")
    hj = doc.get("hooks_json")
    iok = hi.get("ok") if isinstance(hi, dict) else False
    hp = hj.get("present") if isinstance(hj, dict) else False
    hc = hj.get("configured") if isinstance(hj, dict) else False
    print(
        f"Cursor: hook_integrity_ok={iok} hooks.json present={hp} "
        f"configured_for_pyrtkai={hc} overall_ok={doctor_payload_ok(doc)}"
    )
    print(f"Gain tracking: enabled={gain_cfg.enabled} db={gain_cfg.db_path}")
    if aggregate is not None and isinstance(aggregate, dict):
        te = aggregate.get("total_events", 0)
        ts = aggregate.get("tokens_saved_est", 0)
        pct = aggregate.get("tokens_saved_pct_est")
        print(f"Gain aggregate (limit={limit}): events={te} tokens_saved_est={ts} pct={pct}")
    elif gain_cfg.enabled:
        print(f"Gain aggregate (limit={limit}): (no rows yet or empty DB)")
    print("Tip: pyrtkai status --json  |  pyrtkai doctor --json")
    return 0

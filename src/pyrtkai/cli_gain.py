from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from pyrtkai.cli_utils import sanitize_sqlite_limit
from pyrtkai.tracking import (
    connect,
    export_proxy_events_json,
    load_gain_config,
    summarize_proxy_events,
    summarize_proxy_events_for_project,
    summarize_proxy_events_for_project_json,
    summarize_proxy_events_json,
)


def run_gain(args: Namespace) -> int:
    gain_cfg = load_gain_config()
    conn = connect(gain_cfg.db_path)
    try:
        limit = sanitize_sqlite_limit(args.limit)
        if args.gain_cmd in {None, "summary"}:
            if args.json:
                print(summarize_proxy_events_json(conn=conn, limit=limit))
            else:
                print(
                    json.dumps(summarize_proxy_events(conn=conn, limit=limit), indent=2)
                )
        elif args.gain_cmd in {"export", "history"}:
            print(export_proxy_events_json(conn=conn, limit=limit))
        elif args.gain_cmd == "project":
            root = Path(args.project_root).expanduser()
            if args.json:
                print(
                    summarize_proxy_events_for_project_json(
                        conn, project_root=root, limit=limit
                    )
                )
            else:
                print(
                    json.dumps(
                        summarize_proxy_events_for_project(
                            conn=conn, project_root=root, limit=limit
                        ),
                        indent=2,
                        ensure_ascii=False,
                    )
                )
    finally:
        conn.close()
    return 0

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class GainConfig:
    enabled: bool
    db_path: Path
    retention_days: int
    chars_per_token: float = 4.0


def _utc_now_iso() -> str:
    # Fixed-width ISO-8601 makes lexicographic ordering work for UTC timestamps.
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: UP017


def estimate_tokens_from_chars(chars: int, *, chars_per_token: float = 4.0) -> int:
    if chars <= 0:
        return 0
    # Deterministic estimate: 1 token ~ N characters (rough heuristic).
    return int((chars + chars_per_token - 1) // chars_per_token)


def load_gain_config() -> GainConfig:
    enabled = os.environ.get("PYRTKAI_GAIN_ENABLED", "0") in {"1", "true", "TRUE", "yes"}
    db_path_raw = os.environ.get("PYRTKAI_GAIN_DB_PATH", "").strip()
    retention_days_raw = os.environ.get("PYRTKAI_GAIN_RETENTION_DAYS", "30").strip()
    try:
        retention_days = int(retention_days_raw)
    except ValueError:
        retention_days = 30

    if db_path_raw:
        db_path = Path(db_path_raw).expanduser()
    else:
        db_path = (Path.home() / ".pyrtkai" / "gain.sqlite")

    return GainConfig(
        enabled=enabled,
        db_path=db_path,
        retention_days=retention_days,
    )


def _ensure_parent_dir(db_path: Path) -> None:
    parent = db_path.parent
    parent.mkdir(parents=True, exist_ok=True)


def connect(db_path: Path) -> sqlite3.Connection:
    _ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS proxy_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_utc TEXT NOT NULL,
            classification TEXT NOT NULL,
            executed_command TEXT NOT NULL,
            did_fail INTEGER NOT NULL,
            stdout_chars_before INTEGER NOT NULL,
            stdout_chars_after INTEGER NOT NULL,
            stderr_chars_before INTEGER NOT NULL,
            stderr_chars_after INTEGER NOT NULL,
            stdout_tokens_before INTEGER NOT NULL,
            stdout_tokens_after INTEGER NOT NULL,
            stderr_tokens_before INTEGER NOT NULL,
            stderr_tokens_after INTEGER NOT NULL,
            exec_time_ms INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_proxy_events_ts_utc ON proxy_events(ts_utc);"
    )


def apply_retention(conn: sqlite3.Connection, *, retention_days: int) -> None:
    # Store ts_utc as UTC ISO string; lexicographic compare works with fixed-width UTC format.
    try:
        threshold = datetime.now(timezone.utc).timestamp() - (retention_days * 86400)  # noqa: UP017
        threshold_iso = datetime.fromtimestamp(threshold, tz=timezone.utc).strftime(  # noqa: UP017
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except Exception:
        return

    conn.execute("DELETE FROM proxy_events WHERE ts_utc < ?;", (threshold_iso,))


def record_proxy_event(
    *,
    conn: sqlite3.Connection,
    classification: str,
    executed_command: str,
    did_fail: bool,
    stdout_chars_before: int,
    stdout_chars_after: int,
    stderr_chars_before: int,
    stderr_chars_after: int,
    stdout_tokens_before: int,
    stdout_tokens_after: int,
    stderr_tokens_before: int,
    stderr_tokens_after: int,
    exec_time_ms: int,
    ts_utc: str | None = None,
    retention_days: int = 30,
) -> None:
    ensure_schema(conn)
    conn.execute(
        """
        INSERT INTO proxy_events (
            ts_utc,
            classification,
            executed_command,
            did_fail,
            stdout_chars_before,
            stdout_chars_after,
            stderr_chars_before,
            stderr_chars_after,
            stdout_tokens_before,
            stdout_tokens_after,
            stderr_tokens_before,
            stderr_tokens_after,
            exec_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            ts_utc or _utc_now_iso(),
            classification,
            executed_command,
            1 if did_fail else 0,
            stdout_chars_before,
            stdout_chars_after,
            stderr_chars_before,
            stderr_chars_after,
            stdout_tokens_before,
            stdout_tokens_after,
            stderr_tokens_before,
            stderr_tokens_after,
            exec_time_ms,
        ),
    )
    apply_retention(conn, retention_days=retention_days)
    conn.commit()


def summarize_proxy_events(
    *,
    conn: sqlite3.Connection,
    limit: int = 1000,
) -> dict[str, object]:
    ensure_schema(conn)
    cur = conn.execute(
        """
        SELECT
          classification,
          COUNT(*) AS events,
          SUM(stdout_tokens_before + stderr_tokens_before) AS tokens_before,
          SUM(stdout_tokens_after + stderr_tokens_after) AS tokens_after
        FROM proxy_events
        GROUP BY classification
        ORDER BY tokens_before DESC
        LIMIT ?;
        """,
        (limit,),
    )
    rows = cur.fetchall()

    by_class: dict[str, object] = {}
    total_before = 0
    total_after = 0
    total_events = 0
    for row in rows:
        classification = str(row[0])
        events = int(row[1])
        tokens_before = int(row[2] or 0)
        tokens_after = int(row[3] or 0)
        total_events += events
        total_before += tokens_before
        total_after += tokens_after
        by_class[classification] = {
            "events": events,
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "tokens_saved_est": tokens_before - tokens_after,
        }

    return {
        "total_events": total_events,
        "tokens_before": total_before,
        "tokens_after": total_after,
        "tokens_saved_est": total_before - total_after,
        "by_classification": by_class,
    }


def summarize_proxy_events_json(conn: sqlite3.Connection, *, limit: int = 1000) -> str:
    return json.dumps(summarize_proxy_events(conn=conn, limit=limit), ensure_ascii=False)


from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from pyrtkai.cli import main
from pyrtkai.tracking import (
    connect,
    estimate_tokens_from_chars,
    record_proxy_event,
    summarize_proxy_events,
)


def test_estimate_tokens_from_chars_smoke() -> None:
    assert estimate_tokens_from_chars(0) == 0
    assert estimate_tokens_from_chars(1) == 1
    assert estimate_tokens_from_chars(4) == 1
    assert estimate_tokens_from_chars(5) == 2


def test_record_and_summarize_proxy_events(tmp_path: Path) -> None:
    db_path = tmp_path / "gain.sqlite"
    conn = connect(db_path)

    classification = "git"
    executed_command = "git status"
    stdout_chars_before = 100
    stdout_chars_after = 40
    stderr_chars_before = 20
    stderr_chars_after = 10

    stdout_tokens_before = estimate_tokens_from_chars(stdout_chars_before)
    stdout_tokens_after = estimate_tokens_from_chars(stdout_chars_after)
    stderr_tokens_before = estimate_tokens_from_chars(stderr_chars_before)
    stderr_tokens_after = estimate_tokens_from_chars(stderr_chars_after)

    record_proxy_event(
        conn=conn,
        classification=classification,
        executed_command=executed_command,
        did_fail=False,
        stdout_chars_before=stdout_chars_before,
        stdout_chars_after=stdout_chars_after,
        stderr_chars_before=stderr_chars_before,
        stderr_chars_after=stderr_chars_after,
        stdout_tokens_before=stdout_tokens_before,
        stdout_tokens_after=stdout_tokens_after,
        stderr_tokens_before=stderr_tokens_before,
        stderr_tokens_after=stderr_tokens_after,
        exec_time_ms=123,
        retention_days=30,
    )

    summary = summarize_proxy_events(conn=conn, limit=10)
    conn.close()

    assert summary["total_events"] == 1
    tokens_before = stdout_tokens_before + stderr_tokens_before
    tokens_after = stdout_tokens_after + stderr_tokens_after
    assert summary["tokens_before"] == tokens_before
    assert summary["tokens_after"] == tokens_after
    by_class = cast(
        dict[str, dict[str, int]], summary["by_classification"]
    )
    assert by_class[classification]["tokens_saved_est"] == tokens_before - tokens_after


def test_retention_deletes_old_events(tmp_path: Path) -> None:
    db_path = tmp_path / "gain.sqlite"
    conn = connect(db_path)

    record_proxy_event(
        conn=conn,
        classification="ls",
        executed_command="ls -la",
        did_fail=False,
        stdout_chars_before=10,
        stdout_chars_after=10,
        stderr_chars_before=0,
        stderr_chars_after=0,
        stdout_tokens_before=estimate_tokens_from_chars(10),
        stdout_tokens_after=estimate_tokens_from_chars(10),
        stderr_tokens_before=0,
        stderr_tokens_after=0,
        exec_time_ms=1,
        ts_utc="2000-01-01T00:00:00Z",
        retention_days=0,
    )

    summary = summarize_proxy_events(conn=conn, limit=10)
    conn.close()

    assert summary["total_events"] == 0
    assert summary["by_classification"] == {}


def test_gain_summary_cli_empty_db_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "gain.sqlite"
    monkeypatch.setenv("PYRTKAI_GAIN_DB_PATH", str(db_path))
    # Ensure tracking doesn't need to be enabled for summary to work.
    monkeypatch.delenv("PYRTKAI_GAIN_ENABLED", raising=False)

    rc = main(["gain", "summary", "--json"])
    assert rc == 0

    stdout = capsys.readouterr().out.strip()
    payload = json.loads(stdout)
    assert payload["total_events"] == 0


from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from pyrtkai.cli import main
from pyrtkai.tracking import (
    connect,
    estimate_tokens_from_chars,
    load_gain_config,
    record_proxy_event,
    summarize_proxy_events,
    summarize_proxy_events_for_project,
    tokens_saved_pct_est,
)


def test_estimate_tokens_from_chars_smoke() -> None:
    assert estimate_tokens_from_chars(0) == 0
    assert estimate_tokens_from_chars(1) == 1
    assert estimate_tokens_from_chars(4) == 1
    assert estimate_tokens_from_chars(5) == 2


def test_tokens_saved_pct_est_helper() -> None:
    assert tokens_saved_pct_est(tokens_before=0, tokens_saved=0) is None
    assert tokens_saved_pct_est(tokens_before=-1, tokens_saved=0) is None
    assert tokens_saved_pct_est(tokens_before=100, tokens_saved=25) == 25.0
    assert tokens_saved_pct_est(tokens_before=3, tokens_saved=1) == 33.33


def test_summarize_proxy_events_for_project_filters_by_cwd(tmp_path: Path) -> None:
    db_path = tmp_path / "gain.sqlite"
    conn = connect(db_path)
    proj = tmp_path / "myapp"
    proj.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    proj_s = str(proj.resolve())
    other_s = str(other.resolve())

    def _record(cwd: str, classification: str) -> None:
        record_proxy_event(
            conn=conn,
            classification=classification,
            executed_command="x",
            did_fail=False,
            stdout_chars_before=40,
            stdout_chars_after=10,
            stderr_chars_before=0,
            stderr_chars_after=0,
            stdout_tokens_before=estimate_tokens_from_chars(40),
            stdout_tokens_after=estimate_tokens_from_chars(10),
            stderr_tokens_before=0,
            stderr_tokens_after=0,
            exec_time_ms=1,
            cwd=cwd,
            retention_days=30,
        )

    _record(proj_s, "git")
    _record(other_s, "ls")
    sub = proj / "pkg"
    sub.mkdir()
    _record(str(sub.resolve()), "rg")

    summary = summarize_proxy_events_for_project(conn=conn, project_root=proj, limit=50)
    conn.close()

    assert summary["project_root"] == proj_s
    assert summary["total_events"] == 2
    by_class = cast(dict[str, dict[str, object]], summary["by_classification"])
    assert set(by_class) == {"git", "rg"}
    assert "ls" not in by_class


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
    saved = tokens_before - tokens_after
    assert summary["tokens_saved_est"] == saved
    assert summary["tokens_saved_pct_est"] == tokens_saved_pct_est(
        tokens_before=tokens_before,
        tokens_saved=saved,
    )
    by_class = cast(dict[str, dict[str, object]], summary["by_classification"])
    assert by_class[classification]["tokens_saved_est"] == saved
    assert by_class[classification]["tokens_saved_pct_est"] == tokens_saved_pct_est(
        tokens_before=tokens_before,
        tokens_saved=saved,
    )


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
    assert summary["tokens_saved_pct_est"] is None


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
    assert payload["_meta"]["schema"] == "gain_summary"
    assert payload["_meta"]["schema_version"] == 1
    assert payload["total_events"] == 0
    assert payload["tokens_saved_pct_est"] is None


def test_gain_cli_default_summary_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "gain.sqlite"
    monkeypatch.setenv("PYRTKAI_GAIN_DB_PATH", str(db_path))
    monkeypatch.delenv("PYRTKAI_GAIN_ENABLED", raising=False)

    rc = main(["gain", "--json", "--limit", "10"])
    assert rc == 0
    stdout = capsys.readouterr().out.strip()
    payload = json.loads(stdout)
    assert payload["_meta"]["schema"] == "gain_summary"
    assert payload["_meta"]["schema_version"] == 1
    assert payload["total_events"] == 0
    assert payload["tokens_saved_pct_est"] is None


def test_gain_project_cli_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "gain.sqlite"
    proj = tmp_path / "app"
    proj.mkdir()
    conn = connect(db_path)
    record_proxy_event(
        conn=conn,
        classification="git",
        executed_command="git status",
        did_fail=False,
        stdout_chars_before=40,
        stdout_chars_after=10,
        stderr_chars_before=0,
        stderr_chars_after=0,
        stdout_tokens_before=estimate_tokens_from_chars(40),
        stdout_tokens_after=estimate_tokens_from_chars(10),
        stderr_tokens_before=0,
        stderr_tokens_after=0,
        exec_time_ms=1,
        cwd=str(proj.resolve()),
        retention_days=30,
    )
    conn.close()

    monkeypatch.setenv("PYRTKAI_GAIN_DB_PATH", str(db_path))
    monkeypatch.delenv("PYRTKAI_GAIN_ENABLED", raising=False)

    rc = main(["gain", "project", "--root", str(proj), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["_meta"]["schema"] == "gain_project_summary"
    assert payload["_meta"]["schema_version"] == 1
    assert payload["project_root"] == str(proj.resolve())
    assert payload["total_events"] == 1
    assert int(payload["tokens_saved_est"]) > 0


def test_gain_export_cli(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "gain.sqlite"
    conn = connect(db_path)
    record_proxy_event(
        conn=conn,
        classification="git",
        executed_command="git status",
        did_fail=False,
        stdout_chars_before=10,
        stdout_chars_after=5,
        stderr_chars_before=0,
        stderr_chars_after=0,
        stdout_tokens_before=estimate_tokens_from_chars(10),
        stdout_tokens_after=estimate_tokens_from_chars(5),
        stderr_tokens_before=0,
        stderr_tokens_after=0,
        exec_time_ms=1,
        retention_days=30,
    )
    conn.close()

    monkeypatch.setenv("PYRTKAI_GAIN_DB_PATH", str(db_path))
    monkeypatch.setenv("PYRTKAI_GAIN_ENABLED", "0")
    rc = main(["gain", "export", "--limit", "10"])
    assert rc == 0

    stdout = capsys.readouterr().out.strip()
    payload = json.loads(stdout)
    assert isinstance(payload, list)
    assert payload[0]["classification"] == "git"
    assert payload[0]["tokens_saved_est"] >= 0
    assert payload[0]["cwd"] == ""


def test_proxy_tracking_counts_before_after(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "gain.sqlite"
    monkeypatch.setenv("PYRTKAI_GAIN_ENABLED", "1")
    monkeypatch.setenv("PYRTKAI_GAIN_DB_PATH", str(db_path))

    code = "print('A' * 20000)"
    rc = main(["proxy", sys.executable, "-c", code])
    assert rc == 0
    capsys.readouterr()

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT stdout_tokens_before, stdout_tokens_after, cwd "
            "FROM proxy_events ORDER BY id DESC LIMIT 1;"
        ).fetchone()
        assert row is not None
        tokens_before = int(row[0])
        tokens_after = int(row[1])
        assert str(row[2]) == str(Path.cwd().resolve())
        assert tokens_before > 3000
        assert tokens_after < 2000
        assert tokens_before - tokens_after > 2000
    finally:
        conn.close()


def test_gain_export_cli_limit_and_order(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "gain.sqlite"
    conn = connect(db_path)
    try:
        record_proxy_event(
            conn=conn,
            classification="first",
            executed_command="cmd1",
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
            retention_days=30,
        )
        record_proxy_event(
            conn=conn,
            classification="second",
            executed_command="cmd2",
            did_fail=False,
            stdout_chars_before=20,
            stdout_chars_after=5,
            stderr_chars_before=0,
            stderr_chars_after=0,
            stdout_tokens_before=estimate_tokens_from_chars(20),
            stdout_tokens_after=estimate_tokens_from_chars(5),
            stderr_tokens_before=0,
            stderr_tokens_after=0,
            exec_time_ms=1,
            retention_days=30,
        )
    finally:
        conn.close()

    monkeypatch.setenv("PYRTKAI_GAIN_DB_PATH", str(db_path))
    monkeypatch.setenv("PYRTKAI_GAIN_ENABLED", "0")
    rc = main(["gain", "export", "--limit", "1"])
    assert rc == 0

    stdout = capsys.readouterr().out.strip()
    payload = json.loads(stdout)
    assert isinstance(payload, list)
    assert payload[0]["classification"] == "second"


def test_gain_export_negative_limit_returns_empty(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "gain.sqlite"
    conn = connect(db_path)
    try:
        record_proxy_event(
            conn=conn,
            classification="x",
            executed_command="cmd",
            did_fail=False,
            stdout_chars_before=1,
            stdout_chars_after=1,
            stderr_chars_before=0,
            stderr_chars_after=0,
            stdout_tokens_before=estimate_tokens_from_chars(1),
            stdout_tokens_after=estimate_tokens_from_chars(1),
            stderr_tokens_before=0,
            stderr_tokens_after=0,
            exec_time_ms=1,
            retention_days=30,
        )
    finally:
        conn.close()

    monkeypatch.setenv("PYRTKAI_GAIN_DB_PATH", str(db_path))
    monkeypatch.setenv("PYRTKAI_GAIN_ENABLED", "0")

    rc = main(["gain", "export", "--limit", "-1"])
    assert rc == 0

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload == []


def test_gain_history_alias(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "gain.sqlite"
    conn = connect(db_path)
    try:
        record_proxy_event(
            conn=conn,
            classification="hist",
            executed_command="cmd",
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
            retention_days=30,
        )
    finally:
        conn.close()

    monkeypatch.setenv("PYRTKAI_GAIN_DB_PATH", str(db_path))
    monkeypatch.setenv("PYRTKAI_GAIN_ENABLED", "0")

    rc = main(["gain", "history", "--limit", "10"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert isinstance(payload, list)
    assert payload[0]["classification"] == "hist"


def test_chars_per_token_env_affects_token_estimation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "gain.sqlite"
    monkeypatch.setenv("PYRTKAI_GAIN_ENABLED", "1")
    monkeypatch.setenv("PYRTKAI_GAIN_DB_PATH", str(db_path))
    monkeypatch.setenv("PYRTKAI_OUTPUT_MAX_CHARS", "50000")
    monkeypatch.setenv("PYRTKAI_CHARS_PER_TOKEN", "10")

    cfg = load_gain_config()
    assert cfg.chars_per_token == 10.0

    # Avoid truncation: output small and stable.
    code = "print('A' * 100)"
    rc = main(["proxy", sys.executable, "-c", code])
    assert rc == 0

    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT stdout_tokens_before, stdout_tokens_after "
            "FROM proxy_events ORDER BY id DESC LIMIT 1;"
        ).fetchone()
        assert row is not None
        tokens_before = int(row[0])
        tokens_after = int(row[1])
        # No truncation expected, so before==after.
        assert tokens_before == tokens_after
        expected = estimate_tokens_from_chars(101, chars_per_token=10.0)
        assert tokens_before == expected
    finally:
        conn.close()


def test_gain_closes_connection_on_summarize_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: finally must run so SQLite connection is released on handler errors."""
    db_path = tmp_path / "gain.sqlite"
    monkeypatch.setenv("PYRTKAI_GAIN_ENABLED", "1")
    monkeypatch.setenv("PYRTKAI_GAIN_DB_PATH", str(db_path))

    mock_conn = MagicMock()
    with patch("pyrtkai.cli_gain.connect", return_value=mock_conn):
        with patch(
            "pyrtkai.cli_gain.summarize_proxy_events_json",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                main(["gain", "--json"])
    mock_conn.close.assert_called_once()


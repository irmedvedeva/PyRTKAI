from __future__ import annotations

import json

import pytest

from pyrtkai import __version__
from pyrtkai.cli import main


def test_init_json_shape(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["init", "--json"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert data["pyrtkai_version"] == __version__
    assert "python_executable" in data
    assert "next_commands" in data
    assert "easy_start" in data
    es = data["easy_start"]
    assert es.get("target_minutes") == 2
    assert isinstance(es.get("steps"), list)
    assert len(es["steps"]) >= 4
    assert "doctor" not in data


def test_init_quickstart_prints_steps(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["init", "--quickstart"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "easy start" in out.lower()
    assert "Step 1" in out
    assert "Step 4" in out
    assert "-m pyrtkai.cli" in out


def test_init_quickstart_with_doctor_runs_doctor(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PYRTKAI_DENY_REGEXES", raising=False)
    rc = main(["init", "--quickstart", "--with-doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "--- doctor ---" in out


def test_init_json_with_doctor_includes_doctor(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["init", "--json", "--with-doctor"])
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert "doctor" in data
    assert "doctor_exit_code" in data
    assert rc == int(data["doctor_exit_code"])

from __future__ import annotations

import json

import pytest

from pyrtkai import __version__
from pyrtkai.cli import main


def test_status_json_shape(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["status", "--json", "--limit", "5"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["_meta"]["schema"] == "status"
    assert data["_meta"]["schema_version"] == 1
    assert data["pyrtkai_version"] == __version__
    assert "doctor" in data
    assert "gain" in data
    assert data["cursor_ok"] in {True, False}

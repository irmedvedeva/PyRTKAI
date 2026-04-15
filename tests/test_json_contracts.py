from __future__ import annotations

import json

import pytest

from pyrtkai.cli import main


def test_contract_status_json_has_meta(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["status", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["_meta"]["schema"] == "status"
    assert payload["_meta"]["schema_version"] == 1
    assert "doctor" in payload and "gain" in payload


def test_contract_doctor_json_has_meta(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["doctor", "--json"])
    assert rc in {0, 1}
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["_meta"]["schema"] == "doctor"
    assert payload["_meta"]["schema_version"] == 1
    assert "hook_integrity" in payload and "hooks_json" in payload


def test_contract_gain_summary_json_has_meta(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["gain", "summary", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["_meta"]["schema"] == "gain_summary"
    assert payload["_meta"]["schema_version"] == 1
    assert "total_events" in payload and "tokens_saved_est" in payload


def test_contract_rewrite_json_stable_keys(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["rewrite", "--explain", "git", "status"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["action"] == "rewrite"
    assert "reason" in payload and "rewritten_cmd" in payload
    assert payload["rewrite_rule_id"] == "git_status"
    assert "suggested_disable_env" in payload
    assert payload["explain"]["code"] == "rewrite_rule_git_status"

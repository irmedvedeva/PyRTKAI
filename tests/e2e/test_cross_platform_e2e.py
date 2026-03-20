"""
E2E scenarios (ISTQB-style system-level checks, no shell string injection):

- Equivalence: CLI subcommands reachable; rewrite vs skip classes.
- Boundary: empty/malformed hook input fail-closed.
- End-to-end data path: install-equivalent run → proxy → SQLite gain summary.
- Non-functional smoke: bench JSON schema (not SLO thresholds).
- Security: policy deny, invalid deny regex fail-closed, hook script integrity vs baseline.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from pyrtkai.integrity import load_baseline_sha256, sha256_file


@dataclass(frozen=True)
class _ProcResult:
    returncode: int
    stdout: str
    stderr: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _run_pyrtkai(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    timeout_s: float = 120.0,
) -> _ProcResult:
    """Run CLI in a fresh process (same as a user after ``pip install``)."""
    import subprocess  # nosec

    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    proc = subprocess.run(  # nosec
        [sys.executable, "-m", "pyrtkai.cli", *args],
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout_s,
        check=False,
        env=full_env,
    )
    return _ProcResult(proc.returncode, proc.stdout or "", proc.stderr or "")


@pytest.mark.e2e
def test_e2e_first_launch_proxy_help_exits_zero() -> None:
    """First-use surface: subcommand help must work on all platforms."""
    r = _run_pyrtkai(["proxy", "--help"], timeout_s=30.0)
    assert r.returncode == 0
    assert "proxy" in r.stdout.lower() or "execute" in r.stdout.lower()


@pytest.mark.e2e
def test_e2e_rewrite_suggests_proxy_for_supported_command() -> None:
    """Token-savings path: supported command → rewrite action with proxy wrapper."""
    r = _run_pyrtkai(["rewrite", "git", "status"], timeout_s=30.0)
    assert r.returncode == 0
    payload = json.loads(r.stdout.strip())
    assert payload["action"] == "rewrite"
    assert "rewritten_cmd" in payload
    assert "proxy" in str(payload["rewritten_cmd"])
    assert "git" in str(payload["rewritten_cmd"])


@pytest.mark.e2e
def test_e2e_first_proxy_session_records_gain_and_savings_estimate(
    tmp_path: Path,
) -> None:
    """
    Fresh DB + enabled gain: one proxied run with truncation → non-empty summary
    and tokens_saved_est >= 0 with at least one event.
    """
    db = tmp_path / "e2e_gain.sqlite"
    env = {
        "PYRTKAI_GAIN_ENABLED": "1",
        "PYRTKAI_GAIN_DB_PATH": str(db),
        "PYRTKAI_OUTPUT_MAX_CHARS": "400",
        "PYRTKAI_GAIN_RETENTION_DAYS": "7",
    }
    code_print = "print('A' * 8000)"
    r_proxy = _run_pyrtkai(
        ["proxy", sys.executable, "-c", code_print],
        env=env,
        timeout_s=60.0,
    )
    assert r_proxy.returncode == 0
    assert "TRUNCATED" in r_proxy.stdout

    r_gain = _run_pyrtkai(["gain", "--json"], env=env, timeout_s=30.0)
    assert r_gain.returncode == 0
    summary = json.loads(r_gain.stdout.strip())
    assert summary["total_events"] >= 1
    assert "tokens_saved_est" in summary
    assert "tokens_saved_pct_est" in summary
    assert int(summary["tokens_saved_est"]) >= 0
    assert int(summary["tokens_before"]) >= int(summary["tokens_after"])
    pct = summary["tokens_saved_pct_est"]
    assert pct is None or isinstance(pct, (int, float))


@pytest.mark.e2e
def test_e2e_bench_reports_efficiency_metrics_shape() -> None:
    """Efficiency smoke: bench emits comparable latency fields (no fixed SLO)."""
    r = _run_pyrtkai(
        [
            "bench",
            "proxy",
            "--iters",
            "1",
            "--json",
            sys.executable,
            "-c",
            "pass",
        ],
        timeout_s=120.0,
    )
    assert r.returncode == 0
    p = json.loads(r.stdout.strip())
    assert p["direct_exit_code"] == 0
    assert p["proxy_exit_code"] == 0
    assert "direct_avg_ms" in p and "proxy_avg_ms" in p
    assert p["ratio_proxy_to_direct"] is not None


@pytest.mark.e2e
def test_e2e_security_hook_policy_deny_on_regex_match() -> None:
    """Security: deny policy blocks suggested rewrite path (Claude-shaped payload)."""
    env = {"PYRTKAI_DENY_REGEXES": "git"}
    stdin = json.dumps(
        {"hookEventName": "PreToolUse", "tool_input": {"command": "git status"}}
    )
    r = _run_pyrtkai(["hook"], env=env, input_text=stdin, timeout_s=30.0)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    hook_out = out["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    assert hook_out["updatedInput"]["command"] == "git status"


@pytest.mark.e2e
def test_e2e_security_malformed_hook_json_fail_closed() -> None:
    """Security: invalid JSON must not allow execution semantics to slip through."""
    r = _run_pyrtkai(["hook"], input_text="{not json", timeout_s=30.0)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    hook_out = out["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    assert "invalid" in hook_out["permissionDecisionReason"].lower()


@pytest.mark.e2e
def test_e2e_security_invalid_deny_regex_fail_closed() -> None:
    """Security: broken deny config → deny (fail-closed)."""
    env = {"PYRTKAI_DENY_REGEXES": "(*bad"}
    stdin = json.dumps(
        {"hookEventName": "PreToolUse", "tool_input": {"command": "echo ok"}}
    )
    r = _run_pyrtkai(["hook"], env=env, input_text=stdin, timeout_s=30.0)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    hook_out = out["hookSpecificOutput"]
    assert hook_out["permissionDecision"] == "deny"
    assert "policy config error" in hook_out["permissionDecisionReason"]


@pytest.mark.e2e
def test_e2e_security_verify_hook_baseline_matches_bundled_script() -> None:
    """Integrity: bundled Cursor hook script matches checked-in SHA-256 baseline."""
    root = _repo_root()
    script = root / "integrations" / "cursor-plugin" / "scripts" / "pyrtkai-rewrite.sh"
    baseline = root / "integrations" / "cursor-plugin" / "scripts" / ".pyrtkai-rewrite.sh.sha256"
    assert script.is_file() and baseline.is_file()
    expected = load_baseline_sha256(baseline)
    assert expected is not None
    assert sha256_file(script) == expected

    r = _run_pyrtkai(
        [
            "verify-hook",
            "--json",
            "--hook-path",
            str(script),
            "--baseline-path",
            str(baseline),
        ],
        timeout_s=30.0,
    )
    assert r.returncode == 0
    report = json.loads(r.stdout.strip())
    assert report["ok"] is True

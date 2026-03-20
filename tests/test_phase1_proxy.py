from __future__ import annotations

import json
import sys

import pytest

from pyrtkai.cli import main


def test_proxy_exit_code_and_streams(capsys: pytest.CaptureFixture[str]) -> None:
    code = "import sys; print('OUT'); sys.stderr.write('ERR\\n'); sys.exit(3)"
    rc = main(["proxy", sys.executable, "-c", code])
    assert rc == 3

    captured = capsys.readouterr()
    assert "OUT" in captured.out
    assert "ERR" in captured.err


def test_rewrite_placeholder_skip(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["rewrite", "git", "status"])
    assert rc == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "rewrite"
    assert "supported" in payload["reason"] or payload["reason"]
    assert payload["rewritten_cmd"].startswith("pyrtkai proxy git status")


def test_rewrite_skip_when_rtk_disabled(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["rewrite", "RTK_DISABLED=1", "git", "status"])
    assert rc == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "skip"
    assert "RTK_DISABLED" in payload["reason"]


def test_rewrite_skip_on_unbalanced_quotes(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["rewrite", "echo", '"oops'])
    assert rc == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "skip"
    assert "unbalanced quotes" in payload["reason"]


def test_rewrite_skip_on_unsupported_command(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["rewrite", "echo", "hello"])
    assert rc == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "skip"
    assert "unsupported command" in payload["reason"]


def test_rewrite_skip_on_shell_compound_operator(capsys: pytest.CaptureFixture[str]) -> None:
    # Our proxy does not evaluate shell operators (no shell=True).
    rc = main(["rewrite", "echo", "a", "&&", "echo", "b"])
    assert rc == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "skip"
    assert "shell metacharacters" in payload["reason"]


def test_rewrite_skip_on_redirection(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["rewrite", "echo", "hi", ">", "out.txt"])
    assert rc == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "skip"
    assert "shell metacharacters" in payload["reason"]


def test_proxy_truncates_large_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    big = "print('A' * 20000)"
    rc = main(["proxy", sys.executable, "-c", big])
    assert rc == 0

    captured = capsys.readouterr()
    assert "[TRUNCATED]" in captured.out


def test_proxy_pass_through_large_json(capsys: pytest.CaptureFixture[str]) -> None:
    code = "import json; print(json.dumps({'a': 'X' * 20000}))"
    rc = main(["proxy", sys.executable, "-c", code])
    assert rc == 0

    captured = capsys.readouterr()
    assert "[TRUNCATED]" not in captured.out
    assert captured.out.lstrip().startswith("{")
    assert len(captured.out) > 20000


def test_proxy_pass_through_large_ndjson(capsys: pytest.CaptureFixture[str]) -> None:
    code = "import json; [print(json.dumps({'i': i})) for i in range(600)]"
    rc = main(["proxy", sys.executable, "-c", code])
    assert rc == 0

    captured = capsys.readouterr()
    assert "[TRUNCATED]" not in captured.out
    lines = captured.out.strip().splitlines()
    assert len(lines) == 600


from __future__ import annotations

import json
import shlex
import sys
import time

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
    expected_prefix = (
        f"{shlex.quote(sys.executable)} -m pyrtkai.cli proxy git status"
    )
    assert payload["rewritten_cmd"].startswith(expected_prefix)


def test_rewrite_skip_when_rtk_disabled(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["rewrite", "RTK_DISABLED=1", "git", "status"])
    assert rc == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "skip"
    assert "RTK_DISABLED" in payload["reason"]


def test_rewrite_does_not_skip_on_sortk_disabled_false_positive(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # SORTK_DISABLED= must not trigger the RTK_DISABLED gate (substring bug regression).
    rc = main(["rewrite", "SORTK_DISABLED=1", "git", "status"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["action"] == "rewrite"


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


def test_rewrite_skip_on_redirect_variants(capsys: pytest.CaptureFixture[str]) -> None:
    # Ensure our conservative no-shell policy skips common redirect/operator variants.
    variants: list[list[str]] = [
        ["echo", "hi", "2>&1"],  # stderr redirected to stdout
        ["echo", "hi", "2>out.txt"],  # stderr redirect without spaces
        ["echo", "hi", ">out.txt"],  # stdout redirect without spaces
        ["echo", "hi", "2>&", "1"],  # spaced "2>&1" equivalent
        ["echo", "hi", "1>", "out.txt"],  # explicit fd redirect
    ]

    for tokens in variants:
        rc = main(["rewrite", *tokens])
        assert rc == 0
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        assert payload["action"] == "skip"
        assert "shell metacharacters" in payload["reason"]


def test_rewrite_does_not_flag_redirect_inside_quotes(capsys: pytest.CaptureFixture[str]) -> None:
    # '>' inside quotes must not trigger shell metacharacters outside quotes.
    # Command ("echo ...") is unsupported for MVP rewrite; expect "unsupported" reason.
    rc = main(["rewrite", "echo", "'hi", ">", "out.txt'"])
    assert rc == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "skip"
    assert "unsupported command" in payload["reason"]


def test_rewrite_skip_redirect_spacing_corruption_variants(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # These are common "spacing corruption" forms that should be skipped conservatively
    # because our proxy executes without shell evaluation.
    variants: list[list[str]] = [
        ["echo", "hi", "1", ">", "out.txt"],  # 1 > out.txt
        ["echo", "hi", "1", ">out.txt"],  # 1 >out.txt
        ["echo", "hi", "1>", "out.txt"],  # 1> out.txt
        ["echo", "hi", "2", ">", "out.txt"],  # 2 > out.txt
        ["echo", "hi", "2", ">out.txt"],  # 2 >out.txt
        ["echo", "hi", "2>", "out.txt"],  # 2> out.txt
        ["echo", "hi", "2>&", "1"],  # spaced 2>& 1
        ["echo", "hi", "2>&", "1"],  # repeated to keep fixture stable
        ["echo", "hi", "2>", "&1"],  # 2> &1 (no shell)
        ["echo", "hi", "2>", "&", "1"],  # 2> & 1
        ["echo", "hi", "2", ">&", "1"],  # 2 >& 1
        ["echo", "hi", "2", ">&1"],  # 2 >&1
    ]

    for tokens in variants:
        rc = main(["rewrite", *tokens])
        assert rc == 0
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        assert payload["action"] == "skip"
        assert "shell metacharacters" in payload["reason"]


def test_rewrite_does_not_flag_redirect_inside_quotes_spacing_corruption(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # When redirection tokens appear inside quotes, metachar gating must not trigger.
    # 'echo ...' is still unsupported for rewrite mapping, so we expect "unsupported command".
    rc = main(["rewrite", "echo", "'2>&1'"])
    assert rc == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "skip"
    assert "unsupported command" in payload["reason"]


def test_rewrite_mvp_disable_git_status(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYRTKAI_MVP_ENABLE_GIT_STATUS", "0")
    rc = main(["rewrite", "git", "status"])
    assert rc == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "skip"
    assert "unsupported command" in payload["reason"]


def test_rewrite_mvp_disable_ls(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYRTKAI_MVP_ENABLE_LS", "0")
    rc = main(["rewrite", "ls", "-la"])
    assert rc == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["action"] == "skip"
    assert "unsupported command" in payload["reason"]


def test_proxy_truncates_large_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    big = "print('A' * 20000)"
    rc = main(["proxy", sys.executable, "-c", big])
    assert rc == 0

    captured = capsys.readouterr()
    assert "[TRUNCATED]" in captured.out


def test_proxy_respects_output_max_chars_env(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Force aggressive truncation for deterministic behavior.
    monkeypatch.setenv("PYRTKAI_OUTPUT_MAX_CHARS", "100")
    big = "print('A' * 1000)"
    rc = main(["proxy", sys.executable, "-c", big])
    assert rc == 0

    captured = capsys.readouterr()
    assert "[TRUNCATED]" in captured.out


def test_proxy_disable_truncation_when_max_chars_is_large(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYRTKAI_OUTPUT_MAX_CHARS", "50000")
    big = "print('A' * 1000)"
    rc = main(["proxy", sys.executable, "-c", big])
    assert rc == 0

    captured = capsys.readouterr()
    assert "[TRUNCATED]" not in captured.out


def test_proxy_large_text_completes_quickly(capsys: pytest.CaptureFixture[str]) -> None:
    # Streaming proxy should not hang or degrade significantly on large stdout.
    big = "print('A' * 20000)"
    start = time.perf_counter()
    rc = main(["proxy", sys.executable, "-c", big])
    elapsed_s = time.perf_counter() - start
    assert rc == 0
    assert elapsed_s < 2.0

    captured = capsys.readouterr()
    assert "[TRUNCATED]" in captured.out


def test_proxy_truncates_large_stderr_and_preserves_exit_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # When the wrapped process fails, proxy must preserve exit code and still
    # apply truncation markers independently for stderr.
    code = (
        "import sys; "
        "sys.stderr.write('E' * 20000); "
        "sys.exit(7)"
    )
    rc = main(["proxy", sys.executable, "-c", code])
    assert rc == 7

    captured = capsys.readouterr()
    assert "[TRUNCATED]" in captured.err


def test_proxy_streaming_interleaved_stdout_stderr_does_not_hang(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Interleave stdout/stderr writes; proxy should read both streams concurrently.
    code = (
        "import sys, time\n"
        "for i in range(60):\n"
        "  sys.stdout.write(f'OUT{i}\\n'); sys.stdout.flush()\n"
        "  sys.stderr.write(f'ERR{i}\\n'); sys.stderr.flush()\n"
        "  time.sleep(0.002)\n"
    )
    start = time.perf_counter()
    rc = main(["proxy", sys.executable, "-c", code])
    elapsed_s = time.perf_counter() - start

    assert rc == 0
    assert elapsed_s < 3.0

    captured = capsys.readouterr()
    assert "OUT0" in captured.out
    assert "ERR0" in captured.err
    assert "[TRUNCATED]" not in captured.out
    assert "[TRUNCATED]" not in captured.err


def test_proxy_custom_trunc_marker_env(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYRTKAI_OUTPUT_MAX_CHARS", "100")
    monkeypatch.setenv("PYRTKAI_TRUNC_MARKER", "<<CUT>>")
    big = "print('A' * 1000)"

    rc = main(["proxy", sys.executable, "-c", big])
    assert rc == 0

    captured = capsys.readouterr()
    assert "<<CUT>>" in captured.out
    assert "[TRUNCATED]" not in captured.out


def test_proxy_custom_trunc_marker_does_not_break_json(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYRTKAI_OUTPUT_MAX_CHARS", "100")
    monkeypatch.setenv("PYRTKAI_TRUNC_MARKER", "<<CUT>>")
    code = "import json; print(json.dumps({'a': 'X' * 20000}))"

    rc = main(["proxy", sys.executable, "-c", code])
    assert rc == 0

    captured = capsys.readouterr()
    assert "<<CUT>>" not in captured.out
    assert "[TRUNCATED]" not in captured.out
    assert captured.out.lstrip().startswith("{")


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


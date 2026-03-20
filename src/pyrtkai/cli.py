from __future__ import annotations

import argparse
import json
import subprocess  # nosec
import sys
import time

from pyrtkai.contracts import CommandMeta
from pyrtkai.hook import handle_hook_json
from pyrtkai.output_filter import TruncatingOutputFilterEngine, detect_output_format
from pyrtkai.rewriter import get_default_rewriter
from pyrtkai.shell_parse import extract_env_prefix, has_unbalanced_quotes
from pyrtkai.tracking import (
    connect,
    estimate_tokens_from_chars,
    load_gain_config,
    record_proxy_event,
    summarize_proxy_events,
    summarize_proxy_events_json,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pyrtkai")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_proxy = sub.add_parser("proxy", help="Execute command without rewriting (MVP).")
    p_proxy.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command argv to execute (no shell).",
    )

    p_rewrite = sub.add_parser("rewrite", help="Return rewrite decision (MVP placeholder).")
    p_rewrite.add_argument("command_str", nargs=argparse.REMAINDER, help="Original command string.")

    sub.add_parser(
        "hook",
        help="Read hook JSON from stdin and write Claude-style hookSpecificOutput JSON to stdout.",
    )

    p_gain = sub.add_parser("gain", help="Token savings tracking (local).")
    gain_sub = p_gain.add_subparsers(dest="gain_cmd", required=True)
    p_gain_summary = gain_sub.add_parser("summary", help="Summarize saved-token estimates.")
    p_gain_summary.add_argument("--json", action="store_true", help="Print summary as JSON.")
    p_gain_summary.add_argument("--limit", type=int, default=1000, help="Max classifications.")

    args = parser.parse_args(argv)

    if args.cmd == "proxy":
        cmd_argv: list[str] = list(args.command)
        if not cmd_argv:
            return 2

        # Safety: use subprocess with argv list, never shell=True.
        start = time.perf_counter()
        proc = subprocess.run(  # nosec
            cmd_argv,
            text=True,
            capture_output=True,
            check=False,
        )
        exec_time_ms = int((time.perf_counter() - start) * 1000)

        filter_engine = TruncatingOutputFilterEngine()
        did_fail = proc.returncode != 0
        classification = cmd_argv[0]
        gain_cfg = load_gain_config()
        chars_per_token = gain_cfg.chars_per_token

        if proc.stdout:
            meta_out = CommandMeta(
                classification=classification,
                output_format=detect_output_format(proc.stdout),
                did_fail=did_fail,
            )
            filtered_out = filter_engine.filter(proc.stdout, meta=meta_out)
            stdout_chars_before = len(proc.stdout)
            stdout_chars_after = len(filtered_out.output)
            stdout_tokens_before = estimate_tokens_from_chars(
                stdout_chars_before, chars_per_token=chars_per_token
            )
            stdout_tokens_after = estimate_tokens_from_chars(
                stdout_chars_after, chars_per_token=chars_per_token
            )
            sys.stdout.write(filtered_out.output)
        else:
            stdout_chars_before = 0
            stdout_chars_after = 0
            stdout_tokens_before = 0
            stdout_tokens_after = 0

        if proc.stderr:
            meta_err = CommandMeta(
                classification=classification,
                output_format=detect_output_format(proc.stderr),
                did_fail=did_fail,
            )
            filtered_err = filter_engine.filter(proc.stderr, meta=meta_err)
            stderr_chars_before = len(proc.stderr)
            stderr_chars_after = len(filtered_err.output)
            stderr_tokens_before = estimate_tokens_from_chars(
                stderr_chars_before, chars_per_token=chars_per_token
            )
            stderr_tokens_after = estimate_tokens_from_chars(
                stderr_chars_after, chars_per_token=chars_per_token
            )
            sys.stderr.write(filtered_err.output)
        else:
            stderr_chars_before = 0
            stderr_chars_after = 0
            stderr_tokens_before = 0
            stderr_tokens_after = 0

        # Best-effort tracking: never break proxy semantics if tracking fails.
        if gain_cfg.enabled:
            conn = None
            try:
                conn = connect(gain_cfg.db_path)
                record_proxy_event(
                    conn=conn,
                    classification=classification,
                    executed_command=" ".join(cmd_argv),
                    did_fail=did_fail,
                    stdout_chars_before=stdout_chars_before,
                    stdout_chars_after=stdout_chars_after,
                    stderr_chars_before=stderr_chars_before,
                    stderr_chars_after=stderr_chars_after,
                    stdout_tokens_before=stdout_tokens_before,
                    stdout_tokens_after=stdout_tokens_after,
                    stderr_tokens_before=stderr_tokens_before,
                    stderr_tokens_after=stderr_tokens_after,
                    exec_time_ms=exec_time_ms,
                    retention_days=gain_cfg.retention_days,
                )
            except Exception as exc:
                # Fail-open: output has already been written above.
                _ignored_tracking_error = exc  # noqa: F841
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception as exc:
                        _ignored_close_error = exc  # noqa: F841
        return int(proc.returncode)

    if args.cmd == "rewrite":
        command_str = " ".join(args.command_str).strip()
        if not command_str:
            print(json.dumps({"action": "skip", "reason": "empty command"}))
            return 0

        if has_unbalanced_quotes(command_str):
            print(json.dumps({"action": "skip", "reason": "unbalanced quotes"}))
            return 0

        env_prefix, cmd_wo_prefix = extract_env_prefix(command_str)
        rewriter = get_default_rewriter()
        decision = rewriter.rewrite(cmd_wo_prefix, env_prefix)
        payload: dict[str, str | None] = {"action": decision.action, "reason": decision.reason}
        if decision.rewritten_cmd is not None:
            payload["rewritten_cmd"] = decision.rewritten_cmd
        print(json.dumps(payload))
        return 0

    if args.cmd == "hook":
        stdin_json = sys.stdin.read()
        hook_output = handle_hook_json(stdin_json)
        print(json.dumps(hook_output))
        return 0

    if args.cmd == "gain":
        gain_cfg = load_gain_config()
        conn = connect(gain_cfg.db_path)
        if args.gain_cmd == "summary":
            if args.json:
                print(summarize_proxy_events_json(conn=conn, limit=args.limit))
            else:
                print(
                    json.dumps(
                        summarize_proxy_events(conn=conn, limit=args.limit), indent=2
                    )
                )
        conn.close()
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())


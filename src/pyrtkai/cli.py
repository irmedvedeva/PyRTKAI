from __future__ import annotations

import argparse
import json
import subprocess  # nosec
import sys

from pyrtkai.contracts import CommandMeta
from pyrtkai.hook import handle_hook_json
from pyrtkai.output_filter import TruncatingOutputFilterEngine, detect_output_format
from pyrtkai.rewriter import get_default_rewriter
from pyrtkai.shell_parse import extract_env_prefix, has_unbalanced_quotes


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

    args = parser.parse_args(argv)

    if args.cmd == "proxy":
        cmd_argv: list[str] = list(args.command)
        if not cmd_argv:
            return 2

        # Safety: use subprocess with argv list, never shell=True.
        proc = subprocess.run(  # nosec
            cmd_argv,
            text=True,
            capture_output=True,
            check=False,
        )

        filter_engine = TruncatingOutputFilterEngine()
        did_fail = proc.returncode != 0

        if proc.stdout:
            meta_out = CommandMeta(
                classification=cmd_argv[0],
                output_format=detect_output_format(proc.stdout),
                did_fail=did_fail,
            )
            filtered_out = filter_engine.filter(proc.stdout, meta=meta_out)
            sys.stdout.write(filtered_out.output)

        if proc.stderr:
            meta_err = CommandMeta(
                classification=cmd_argv[0],
                output_format=detect_output_format(proc.stderr),
                did_fail=did_fail,
            )
            filtered_err = filter_engine.filter(proc.stderr, meta=meta_err)
            sys.stderr.write(filtered_err.output)
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

    return 2


if __name__ == "__main__":
    raise SystemExit(main())


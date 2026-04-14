from __future__ import annotations

import argparse

from pyrtkai import __version__
from pyrtkai.cli_bench import run_bench_proxy
from pyrtkai.cli_config import run_config
from pyrtkai.cli_doctor import run_doctor
from pyrtkai.cli_gain import run_gain
from pyrtkai.cli_hook import run_hook
from pyrtkai.cli_proxy import run_proxy
from pyrtkai.cli_rewrite import run_rewrite
from pyrtkai.cli_verify_hook import run_verify_hook


class _HelpFormatter(
    argparse.RawDescriptionHelpFormatter,
    argparse.ArgumentDefaultsHelpFormatter,
):
    """Preserve epilog newlines and show defaults."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pyrtkai",
        formatter_class=_HelpFormatter,
        description=(
            "Local CLI layer for AI-driven terminals: no-shell proxy, hooks, "
            "output filtering, and policy gate (see README on PyPI)."
        ),
        epilog=(
            "Quick examples:\n"
            "  pyrtkai doctor --json\n"
            "  pyrtkai proxy python3 -c \"print('ok')\"\n"
            "  pyrtkai rewrite git status\n"
            "  printf '%s' '{\"tool_input\":{\"command\":\"echo hi\"}}' | pyrtkai hook\n"
            "  pyrtkai bench proxy --iters 5 -- python3 -c \"print(1)\"\n"
            "\n"
            f"Version: {__version__}"
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser(
        "proxy",
        help="Execute command without rewriting (MVP).",
    ).add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command argv to execute (no shell).",
    )

    sub.add_parser(
        "rewrite",
        help="Return rewrite decision (MVP placeholder).",
    ).add_argument("command_str", nargs=argparse.REMAINDER, help="Original command string.")

    sub.add_parser(
        "hook",
        help="Read hook JSON from stdin and write Claude-style hookSpecificOutput JSON to stdout.",
    )

    p_verify = sub.add_parser(
        "verify-hook",
        help="Verify the installed Cursor hook integrity (SHA-256 baseline, fail-closed).",
    )
    p_verify.add_argument(
        "--hook-path",
        default="",
        help="Path to the hook script file (default: ~/.cursor/hooks/pyrtkai-rewrite.sh).",
    )
    p_verify.add_argument(
        "--baseline-path",
        default="",
        help="Path to the stored SHA-256 baseline file.",
    )
    p_verify.add_argument("--json", action="store_true", help="Print result as JSON.")

    sub.add_parser(
        "doctor",
        help="Check Cursor hook + configuration health (local).",
    ).add_argument("--json", action="store_true", help="Print result as JSON.")

    p_config = sub.add_parser(
        "config",
        help="Show local configuration relevant to PyRTKAI (MVP rewrite rules enabled).",
    )
    p_config.add_argument("--json", action="store_true", help="Print result as JSON.")

    p_gain = sub.add_parser("gain", help="Token savings tracking (local).")
    p_gain.add_argument("--json", action="store_true", help="Print output as JSON.")
    p_gain.add_argument(
        "--limit", type=int, default=1000, help="Max items for summary/export."
    )
    gain_sub = p_gain.add_subparsers(dest="gain_cmd")
    p_gain_summary = gain_sub.add_parser("summary", help="Summarize saved-token estimates.")
    p_gain_summary.add_argument("--json", action="store_true", help="Print summary as JSON.")
    p_gain_summary.add_argument("--limit", type=int, default=1000, help="Max classifications.")

    p_gain_export = gain_sub.add_parser(
        "export", help="Export recent proxy events as JSON (local)."
    )
    p_gain_export.add_argument("--limit", type=int, default=1000, help="Max events.")

    p_gain_history = gain_sub.add_parser(
        "history", help="Alias for export (recent proxy events as JSON)."
    )
    p_gain_history.add_argument("--limit", type=int, default=1000, help="Max events.")

    p_gain_project = gain_sub.add_parser(
        "project",
        help="Summarize token savings for proxy runs under a project directory (cwd).",
    )
    p_gain_project.add_argument(
        "--root",
        default=".",
        dest="project_root",
        metavar="PATH",
        help="Project root path (default: current working directory).",
    )
    p_gain_project.add_argument(
        "--json", action="store_true", help="Print result as one-line JSON."
    )
    p_gain_project.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Max classification groups (SQL LIMIT after GROUP BY).",
    )

    p_bench = sub.add_parser("bench", help="Benchmark proxy overhead (local).")
    bench_sub = p_bench.add_subparsers(dest="bench_cmd", required=True)
    p_bench_proxy = bench_sub.add_parser("proxy", help="Bench direct exec vs proxy.")
    p_bench_proxy.add_argument("--iters", type=int, default=5, help="Iterations.")
    p_bench_proxy.add_argument("--json", action="store_true", help="Print as JSON.")
    p_bench_proxy.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command argv to execute (no shell).",
    )

    args = parser.parse_args(argv)

    if args.cmd == "verify-hook":
        return run_verify_hook(args)
    if args.cmd == "doctor":
        return run_doctor(args)
    if args.cmd == "config":
        return run_config(args)
    if args.cmd == "bench" and args.bench_cmd == "proxy":
        return run_bench_proxy(args)
    if args.cmd == "proxy":
        return run_proxy(args)
    if args.cmd == "rewrite":
        return run_rewrite(args)
    if args.cmd == "hook":
        return run_hook()
    if args.cmd == "gain":
        return run_gain(args)

    raise RuntimeError(
        f"unhandled pyrtkai subcommand (add a dispatch branch): {args.cmd!r}"
    )


if __name__ == "__main__":
    raise SystemExit(main())

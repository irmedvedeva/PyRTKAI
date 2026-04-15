from __future__ import annotations

import argparse
from collections.abc import Callable

from pyrtkai import __version__
from pyrtkai.cli_bench import run_bench_proxy
from pyrtkai.cli_config import run_config
from pyrtkai.cli_doctor import run_doctor
from pyrtkai.cli_gain import run_gain
from pyrtkai.cli_hook import run_hook
from pyrtkai.cli_init import run_init
from pyrtkai.cli_proxy import run_proxy
from pyrtkai.cli_rewrite import run_rewrite
from pyrtkai.cli_status import run_status
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
            "  pyrtkai init --quickstart\n"
            "  pyrtkai status --json\n"
            "  pyrtkai doctor --json\n"
            "  pyrtkai proxy python3 -c \"print('ok')\"\n"
            "  pyrtkai proxy --summary -- python3 -c \"print('x'*8000)\"\n"
            "  pyrtkai rewrite git status\n"
            "  printf '%s' '{\"tool_input\":{\"command\":\"echo hi\"}}' | pyrtkai hook\n"
            "  pyrtkai bench proxy --iters 5 -- python3 -c \"print(1)\"\n"
            "\n"
            f"Version: {__version__}"
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_proxy = sub.add_parser(
        "proxy",
        help="Execute command without rewriting (MVP).",
    )
    p_proxy.add_argument(
        "--summary",
        action="store_true",
        help=(
            "After the run, print one-line estimated output savings to stderr "
            "(char + token heuristics)."
        ),
    )
    p_proxy.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help=(
            "Command argv to execute (no shell). Put flags before the program "
            "(e.g. pyrtkai proxy --summary -- python3 -c \"print(1)\")."
        ),
    )

    p_rewrite = sub.add_parser(
        "rewrite",
        help="Return rewrite decision (MVP placeholder).",
    )
    p_rewrite.add_argument(
        "--explain",
        action="store_true",
        help=(
            "Include machine-readable explain block (code, why, remediation) "
            "in JSON when skipping."
        ),
    )
    p_rewrite.add_argument(
        "command_str",
        nargs=argparse.REMAINDER,
        help="Original command string.",
    )

    sub.add_parser(
        "hook",
        help="Read hook JSON from stdin and write Claude-style hookSpecificOutput JSON to stdout.",
    )

    p_init = sub.add_parser(
        "init",
        help="Onboarding: show version, interpreter, and next steps (optional doctor).",
    )
    p_init.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    p_init.add_argument(
        "--with-doctor",
        action="store_true",
        help="Run pyrtkai doctor after the summary (exit code follows doctor when set).",
    )
    p_init.add_argument(
        "--quickstart",
        action="store_true",
        help=(
            "Print a short guided path (~2 min): proxy, truncation demo, hook, status/doctor."
        ),
    )

    p_status = sub.add_parser(
        "status",
        help="One-screen summary: version, Cursor hook health, optional gain aggregates.",
    )
    p_status.add_argument("--json", action="store_true", help="Print JSON.")
    p_status.add_argument(
        "--limit",
        type=int,
        default=1000,
        metavar="N",
        help="Max classification groups when summarizing gain (SQL LIMIT).",
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

    dispatch_table: dict[str, Callable[[argparse.Namespace], int]] = {
        "verify-hook": run_verify_hook,
        "init": run_init,
        "status": run_status,
        "doctor": run_doctor,
        "config": run_config,
        "proxy": run_proxy,
        "rewrite": run_rewrite,
        "gain": run_gain,
        "hook": lambda _args: run_hook(),
    }

    if args.cmd == "bench":
        if getattr(args, "bench_cmd", None) == "proxy":
            return run_bench_proxy(args)
        raise RuntimeError(
            f"unhandled pyrtkai subcommand (add a dispatch branch): {args.cmd!r}"
        )

    handler = dispatch_table.get(args.cmd)
    if handler is not None:
        return handler(args)

    raise RuntimeError(
        f"unhandled pyrtkai subcommand (add a dispatch branch): {args.cmd!r}"
    )


if __name__ == "__main__":
    raise SystemExit(main())

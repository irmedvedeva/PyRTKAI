"""Onboarding: print interpreter + version and next steps (optional doctor)."""

from __future__ import annotations

import io
import json
import os
import shlex
import sys
from argparse import Namespace
from contextlib import redirect_stdout
from typing import Any

from pyrtkai import __version__
from pyrtkai.cli_doctor import run_doctor
from pyrtkai.schema_meta import SCHEMA_INIT, build_schema_meta


def _cli_module_invocation() -> str:
    """Argv-safe prefix so copy-paste works when `pyrtkai` is not on PATH."""
    return f"{shlex.quote(sys.executable)} -m pyrtkai.cli"


def _easy_start_block() -> dict[str, Any]:
    """
    Short, copy-paste path to first success (proxy + visible truncation + hook + checks).

    Commands use `python -m pyrtkai.cli` so they work from the current interpreter/venv.
    """
    cli = _cli_module_invocation()
    py = shlex.quote(sys.executable)
    print_ok = shlex.quote("print('ok')")
    print_big = shlex.quote("print('x' * 400)")
    hook_in = '{"tool_input":{"command":"echo hi"}}'

    steps: list[dict[str, Any]] = [
        {
            "id": 1,
            "title": "Run the proxy (expect: ok on stdout)",
            "commands": [f"{cli} proxy {py} -c {print_ok}"],
        },
        {
            "id": 2,
            "title": "See truncation + optional savings line (stderr)",
            "commands": [
                f"PYRTKAI_OUTPUT_MAX_CHARS=120 {cli} proxy --summary -- {py} -c {print_big}",
            ],
        },
        {
            "id": 3,
            "title": "Try the stdin/stdout hook adapter",
            "commands": [f"printf '%s' {shlex.quote(hook_in)} | {cli} hook"],
        },
        {
            "id": 4,
            "title": "Verify install (JSON)",
            "commands": [
                f"{cli} status --json",
                f"{cli} doctor --json",
            ],
        },
    ]

    return {
        "about": (
            "Commands use `python -m pyrtkai.cli` so they work without `pyrtkai` on PATH."
        ),
        "target_minutes": 2,
        "steps": steps,
    }


def _print_quickstart_guide() -> None:
    block = _easy_start_block()
    print("PyRTKAI — easy start (~2 minutes)")
    print("=================================")
    print(block["about"])
    print()
    for step in block["steps"]:
        sid = step["id"]
        title = step["title"]
        cmds = step["commands"]
        print(f"Step {sid} — {title}")
        for line in cmds:
            print(f"  {line}")
        print()
    print("IDE hooks (merge into hooks.json): see integrations/cursor-plugin/README.md")


def _build_payload(with_doctor: bool) -> dict[str, Any]:
    exe = sys.executable
    pyrtkai_python = os.environ.get("PYRTKAI_PYTHON", "").strip() or None
    base: dict[str, Any] = {
        "_meta": build_schema_meta(SCHEMA_INIT),
        "pyrtkai_version": __version__,
        "python_version": sys.version.split()[0],
        "python_executable": exe,
        "pyrtkai_python_env": pyrtkai_python,
        "recommended_pyrtkai_python_export": f'export PYRTKAI_PYTHON="{exe}"',
        "easy_start": _easy_start_block(),
        "next_commands": [
            "pyrtkai status --json",
            "pyrtkai doctor --json",
            'pyrtkai proxy python3 -c "print(\'ok\')"',
            'printf \'%s\' \'{"tool_input":{"command":"echo hi"}}\' | pyrtkai hook',
        ],
        "cursor_plugin_readme": "integrations/cursor-plugin/README.md",
    }
    if with_doctor:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_doctor(Namespace(json=True))
        raw = buf.getvalue().strip()
        try:
            base["doctor"] = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            base["doctor"] = {"error": "doctor did not emit JSON", "raw": raw[:500]}
        base["doctor_exit_code"] = code
    return base


def run_init(args: Namespace) -> int:
    with_doctor = bool(getattr(args, "with_doctor", False))
    quickstart = bool(getattr(args, "quickstart", False))
    if args.json:
        data = _build_payload(with_doctor)
        print(json.dumps(data, ensure_ascii=False))
        if with_doctor:
            return int(data.get("doctor_exit_code", 1))
        return 0

    if quickstart:
        print(f"pyrtkai {__version__}  |  Python {sys.version.split()[0]}")
        print(f"Interpreter: {sys.executable}")
        pyrtkai_python = os.environ.get("PYRTKAI_PYTHON", "").strip()
        if pyrtkai_python:
            print(f"PYRTKAI_PYTHON is set: {pyrtkai_python}")
        else:
            print(
                "Tip: for IDE hooks, set PYRTKAI_PYTHON to this interpreter (absolute path):",
                file=sys.stderr,
            )
            print(f'  export PYRTKAI_PYTHON="{sys.executable}"', file=sys.stderr)
        print()
        _print_quickstart_guide()
        print()
        if with_doctor:
            print("--- doctor ---")
            run_doctor(Namespace(json=False))
            # Onboarding quickstart should stay non-blocking: doctor output informs,
            # but missing local hook setup must not fail the init command.
            return 0
        return 0

    print("PyRTKAI init")
    print("===========")
    print(f"pyrtkai {__version__}  |  Python {sys.version.split()[0]}")
    print(f"Interpreter: {sys.executable}")
    pyrtkai_python = os.environ.get("PYRTKAI_PYTHON", "").strip()
    if pyrtkai_python:
        print(f"PYRTKAI_PYTHON is set: {pyrtkai_python}")
    else:
        print(
            "Tip: for Cursor hooks, set PYRTKAI_PYTHON to this interpreter (absolute path):",
            file=sys.stderr,
        )
        print(f'  export PYRTKAI_PYTHON="{sys.executable}"', file=sys.stderr)

    print()
    print("Next commands:")
    for cmd in (
        "pyrtkai init --quickstart",
        "pyrtkai status --json",
        "pyrtkai doctor --json",
        'pyrtkai proxy python3 -c "print(\'ok\')"',
    ):
        print(f"  {cmd}")
    print()
    print("Guided path (~2 min, copy-paste):  pyrtkai init --quickstart")
    print()
    print("Cursor bundle (hooks, merge into ~/.cursor/hooks.json):")
    print("  integrations/cursor-plugin/README.md")
    print()

    if with_doctor:
        print("--- doctor ---")
        return run_doctor(Namespace(json=False))

    return 0

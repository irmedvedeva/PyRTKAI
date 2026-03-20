from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CmdResult:
    returncode: int
    stdout: str
    stderr: str


def run_command(
    args: list[str],
    *,
    input_text: str | None = None,
    timeout_s: float = 10.0,
) -> CmdResult:
    """
    Test harness for running a subprocess with args (no shell string construction).
    """
    proc = subprocess.run(
        args,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout_s,
        check=False,
    )
    return CmdResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


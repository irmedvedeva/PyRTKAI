from __future__ import annotations

import subprocess  # nosec
import sys
import threading
import time
from argparse import Namespace
from collections.abc import Callable
from typing import Any

from pyrtkai.output_filter import create_output_filter_engine
from pyrtkai.tracking import (
    connect,
    estimate_tokens_from_chars,
    load_gain_config,
    record_proxy_event,
)


def run_proxy(args: Namespace) -> int:
    proxy_cmd_argv: list[str] = list(args.command)
    if not proxy_cmd_argv:
        return 2

    # Safety: use subprocess with argv list, never shell=True.
    start = time.perf_counter()
    proc = subprocess.Popen(  # nosec
        proxy_cmd_argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        bufsize=0,
    )

    filter_engine = create_output_filter_engine()
    max_chars = filter_engine.max_chars
    trunc_marker = filter_engine.trunc_marker
    half = max_chars // 2

    classification = proxy_cmd_argv[0]
    gain_cfg = load_gain_config()
    chars_per_token = gain_cfg.chars_per_token

    stdout_lock = threading.Lock()
    stderr_lock = threading.Lock()

    def write_stdout(s: str) -> None:
        with stdout_lock:
            sys.stdout.write(s)

    def write_stderr(s: str) -> None:
        with stderr_lock:
            sys.stderr.write(s)

    def read_and_filter(
        stream: Any, write_func: Callable[[str], None]
    ) -> dict[str, int]:
        """
        Stream-safe filter:
        - If output starts with JSON ('{' or '[' after leading whitespace'):
          pass-through unchanged.
        - Otherwise: for text, keep first+last part with a deterministic truncation marker.
          We never buffer unbounded text; worst-case stores <= max_chars+chunk_size.
        """
        probe = ""
        mode: str | None = None  # "passthrough" | "text" | None

        # "before" counts total chars from original stream.
        total_chars_before = 0

        # "after" counts chars that we actually write.
        total_chars_after: int = 0

        # Text truncation state
        full: str = ""
        truncated = False
        head = ""
        tail = ""

        # Upper bound for whitespace-only probe before deciding.
        max_probe_chars = max(8192, max_chars)

        while True:
            chunk = stream.read(4096)
            if not chunk:
                break

            total_chars_before += len(chunk)

            if mode is None:
                probe += chunk

                stripped = probe.lstrip()
                if stripped:
                    first = stripped[0]
                    if first in {"{", "["}:
                        mode = "passthrough"
                        total_chars_after += len(probe)
                        write_func(probe)
                        probe = ""
                    else:
                        mode = "text"
                        full = probe
                        probe = ""
                        if len(full) > max_chars:
                            truncated = True
                            head = full[:half]
                            tail = full[-half:]
                            full = ""
                elif len(probe) > max_probe_chars:
                    # Treat as text if whitespace-only probe grows too large.
                    mode = "text"
                    full = probe
                    probe = ""
                    if len(full) > max_chars:
                        truncated = True
                        head = full[:half]
                        tail = full[-half:]
                        full = ""

                continue

            if mode == "passthrough":
                write_func(chunk)
                total_chars_after += len(chunk)
                continue

            # mode == "text"
            if not truncated:
                full += chunk
                total_chars_after = 0  # recalculated at end
                if len(full) > max_chars:
                    truncated = True
                    head = full[:half]
                    tail = full[-half:]
                    full = ""
            else:
                tail = (tail + chunk)[-half:]

        if mode == "passthrough":
            return {"chars_before": total_chars_before, "chars_after": total_chars_after}

        # mode == "text"
        if not truncated:
            write_func(full)
            total_chars_after = len(full)
        else:
            # head + marker + tail
            write_func(head + trunc_marker + tail)
            total_chars_after = len(head) + len(trunc_marker) + len(tail)

        return {"chars_before": total_chars_before, "chars_after": total_chars_after}

    stdout_counts: dict[str, int] = {"chars_before": 0, "chars_after": 0}
    stderr_counts: dict[str, int] = {"chars_before": 0, "chars_after": 0}

    stdout_stream = proc.stdout
    stderr_stream = proc.stderr
    if stdout_stream is None or stderr_stream is None:
        # Should not happen; fail closed to original behavior.
        out, err = proc.communicate()
        stdout_counts = {"chars_before": len(out or ""), "chars_after": len(out or "")}
        stderr_counts = {"chars_before": len(err or ""), "chars_after": len(err or "")}
        sys.stdout.write(out or "")
        sys.stderr.write(err or "")
    else:
        stdout_thread = threading.Thread(
            target=lambda: stdout_counts.update(
                read_and_filter(stdout_stream, write_stdout)
            ),
        )
        stderr_thread = threading.Thread(
            target=lambda: stderr_counts.update(
                read_and_filter(stderr_stream, write_stderr)
            ),
        )

        stdout_thread.start()
        stderr_thread.start()
        proc.wait()
        stdout_thread.join()
        stderr_thread.join()

    exec_time_ms = int((time.perf_counter() - start) * 1000)
    did_fail = proc.returncode != 0

    stdout_chars_before = stdout_counts["chars_before"]
    stdout_chars_after = stdout_counts["chars_after"]
    stderr_chars_before = stderr_counts["chars_before"]
    stderr_chars_after = stderr_counts["chars_after"]

    stdout_tokens_before = estimate_tokens_from_chars(
        stdout_chars_before, chars_per_token=chars_per_token
    )
    stdout_tokens_after = estimate_tokens_from_chars(
        stdout_chars_after, chars_per_token=chars_per_token
    )
    stderr_tokens_before = estimate_tokens_from_chars(
        stderr_chars_before, chars_per_token=chars_per_token
    )
    stderr_tokens_after = estimate_tokens_from_chars(
        stderr_chars_after, chars_per_token=chars_per_token
    )

    # Best-effort tracking: never break proxy semantics if tracking fails.
    if gain_cfg.enabled:
        conn = None
        try:
            conn = connect(gain_cfg.db_path)
            record_proxy_event(
                conn=conn,
                classification=classification,
                executed_command=" ".join(proxy_cmd_argv),
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
            # Fail-open: output has already been written.
            _ignored_tracking_error = exc  # noqa: F841
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception as exc:
                    _ignored_close_error = exc  # noqa: F841

    return int(proc.returncode)

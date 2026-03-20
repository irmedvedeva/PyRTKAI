from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from pyrtkai.contracts import CommandMeta, FilterResult, OutputFilterEngine


def detect_output_format(output: str) -> Literal["text", "json", "ndjson"]:
    stripped = output.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    if "\n" in stripped and all(
        line.strip().startswith("{")
        for line in stripped.splitlines()[:50]
        if line.strip()
    ):
        return "ndjson"
    return "text"


@dataclass(frozen=True)
class TruncatingOutputFilterEngine(OutputFilterEngine):
    """
    Safe MVP filter:
    - For text outputs: if too large, keep first+last part with a marker.
    - For JSON/NDJSON: pass through unchanged (format safety).
    """

    max_chars: int = 4000
    trunc_marker: str = "\n...[TRUNCATED]...\n"

    def filter(self, output: str, meta: CommandMeta) -> FilterResult:
        if meta.output_format in {"json", "ndjson"}:
            return FilterResult(output=output, did_modify=False)

        if len(output) <= self.max_chars:
            return FilterResult(output=output, did_modify=False)

        # Keep start + end; deterministic, does not reorder content.
        head = output[: self.max_chars // 2]
        tail = output[-(self.max_chars // 2) :]
        filtered = head + self.trunc_marker + tail
        return FilterResult(output=filtered, did_modify=True)


def load_output_filter_config() -> tuple[int, str]:
    """
    User-facing configuration for output truncation.

    Env:
      - PYRTKAI_OUTPUT_MAX_CHARS: int >= 0
      - PYRTKAI_TRUNC_MARKER: marker string (optional)
    """
    max_chars_raw = os.environ.get("PYRTKAI_OUTPUT_MAX_CHARS", "").strip()
    max_chars = 4000
    if max_chars_raw:
        try:
            max_chars_candidate = int(max_chars_raw)
            if max_chars_candidate >= 0:
                max_chars = max_chars_candidate
        except ValueError:
            pass

    trunc_marker = os.environ.get(
        "PYRTKAI_TRUNC_MARKER", "\n...[TRUNCATED]...\n"
    )  # keep default if unset/invalid

    return max_chars, trunc_marker


def load_output_filter_profile() -> str:
    """
    Select the output filter profile.

    Env:
      - PYRTKAI_OUTPUT_FILTER_PROFILE: string (default: "truncating")
    """
    profile = os.environ.get("PYRTKAI_OUTPUT_FILTER_PROFILE", "truncating").strip()
    return profile.lower() if profile else "truncating"


def create_output_filter_engine() -> TruncatingOutputFilterEngine:
    profile = load_output_filter_profile()
    max_chars, trunc_marker = load_output_filter_config()

    # MVP only supports truncating filter; unknown profiles fall back safely.
    if profile != "truncating":
        profile = "truncating"

    return TruncatingOutputFilterEngine(max_chars=max_chars, trunc_marker=trunc_marker)


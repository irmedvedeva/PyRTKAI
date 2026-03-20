from __future__ import annotations

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


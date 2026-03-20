from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class RewriteDecision:
    action: Literal["rewrite", "pass", "skip"]
    rewritten_cmd: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class CommandMeta:
    classification: str
    output_format: Literal["text", "json", "ndjson"] = "text"
    did_fail: bool = False


@dataclass(frozen=True)
class FilterResult:
    output: str
    did_modify: bool


class CommandRewriter(Protocol):
    def rewrite(self, cmd: str, env_prefix: str) -> RewriteDecision: ...


class OutputFilterEngine(Protocol):
    def filter(self, output: str, meta: CommandMeta) -> FilterResult: ...


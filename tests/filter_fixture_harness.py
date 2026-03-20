from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

from pyrtkai.contracts import CommandMeta


class OutputFilterExpect(TypedDict, total=False):
    did_modify: bool
    marker_present: bool
    unchanged: bool


@dataclass(frozen=True)
class OutputFilterCase:
    case_id: str
    input_format: Literal["text", "json", "ndjson"]
    generator: dict[str, Any]
    expect: OutputFilterExpect


def _default_fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "output_filter_cases.json"


def load_output_filter_cases(
    fixture_path: Path | None = None,
) -> list[OutputFilterCase]:
    path = fixture_path or _default_fixture_path()
    raw = json.loads(path.read_text(encoding="utf-8"))

    cases: list[OutputFilterCase] = []
    for item in raw:
        cases.append(
            OutputFilterCase(
                case_id=str(item["id"]),
                input_format=cast(
                    Literal["text", "json", "ndjson"], item["input_format"]
                ),
                generator=cast(dict[str, Any], item["generator"]),
                expect=cast(OutputFilterExpect, item["expect"]),
            )
        )
    return cases


def meta_from_output_format(
    output_format: Literal["text", "json", "ndjson"],
) -> CommandMeta:
    # did_fail does not matter for MVP output filter tests.
    return CommandMeta(classification="fixture", output_format=output_format, did_fail=False)


def generate_output_from_case(case: OutputFilterCase) -> str:
    kind = cast(str, case.generator.get("kind"))
    if kind == "prefix_suffix":
        gen = case.generator
        length = int(gen["length"])
        prefix = str(gen["prefix"])
        suffix = str(gen["suffix"])
        middle = str(gen["middle"])
        if len(prefix) != 1 or len(suffix) != 1:
            prefix = prefix[:1]
            suffix = suffix[:1]
        if length <= 2:
            return prefix[:length]
        return prefix + (middle * (length - 2)) + suffix

    if kind == "json_object":
        gen = case.generator
        size = int(gen["size"])
        payload = {"a": "X" * max(1, size - 20)}
        return json.dumps(payload)

    if kind == "ndjson":
        gen = case.generator
        lines = int(gen["lines"])
        line_size = int(gen["line_size"])
        objs = [{"i": i, "v": "X" * max(1, line_size - 20)} for i in range(lines)]
        return "\n".join(json.dumps(o, separators=(",", ":")) for o in objs) + "\n"

    raise AssertionError(f"Unknown generator kind: {kind!r}")


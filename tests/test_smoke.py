from __future__ import annotations

from pyrtkai.contracts import CommandMeta, FilterResult, RewriteDecision


def test_contract_dataclasses_smoke() -> None:
    d = RewriteDecision(action="skip", reason="ok")
    assert d.action == "skip"

    meta = CommandMeta(classification="git", output_format="text", did_fail=False)
    assert meta.classification == "git"

    r = FilterResult(output="x", did_modify=False)
    assert r.output == "x"


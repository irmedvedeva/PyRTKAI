"""
Regression: fd merge / redirect spellings (e.g. 2>&1) must not be 'rewritten' —
skip with metachar gate.
"""

from __future__ import annotations

import json
from typing import cast

import pytest

from pyrtkai.cli import main
from pyrtkai.shell_parse import has_shell_metacharacters_outside_quotes


@pytest.mark.parametrize(
    "command_str,expect_meta",
    [
        ("git status 2>&1", True),
        ("git status 2> &1", True),
        ("git status 2 > &1", True),
        ("git status > log.txt 2>&1", True),
        ("GIT_PAGER=cat git status 2>&1", True),
        ("git status", False),
    ],
)
def test_shell_metachar_detects_fd_redirect_variants(command_str: str, expect_meta: bool) -> None:
    assert has_shell_metacharacters_outside_quotes(command_str) is expect_meta


@pytest.mark.parametrize(
    "tokens",
    [
        ["git", "status", "2>&1"],
        ["git", "status", "2>", "&1"],
        ["git", "status", "2", ">&1"],
        ["git", "status", "2", ">", "&1"],
        ["GIT_PAGER=cat", "git", "status", "2>&1"],
    ],
)
def test_rewrite_skips_when_stderr_merge_present(
    tokens: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["rewrite", *tokens])
    assert rc == 0
    payload = cast(dict[str, object], json.loads(capsys.readouterr().out.strip()))
    assert payload["action"] == "skip"
    assert "shell metacharacters" in str(payload.get("reason", ""))


def test_rewrite_still_allowed_plain_git_status(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["rewrite", "git", "status"])
    assert rc == 0
    payload = cast(dict[str, object], json.loads(capsys.readouterr().out.strip()))
    assert payload["action"] == "rewrite"

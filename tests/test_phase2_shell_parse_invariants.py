from __future__ import annotations

import json
import random
from typing import cast

import pytest

from pyrtkai.cli import main


def _rand_token(rng: random.Random, *, min_len: int = 1, max_len: int = 10) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789_"
    n = rng.randint(min_len, max_len)
    return "".join(rng.choice(alphabet) for _ in range(n))


def _call_rewrite(tokens: list[str], capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    rc = main(["rewrite", *tokens])
    assert rc == 0
    captured = capsys.readouterr()
    return cast(dict[str, object], json.loads(captured.out.strip()))


def test_bounded_unbalanced_quotes_are_skipped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rng = random.Random(1338)
    for _ in range(50):
        token = _rand_token(rng, min_len=1, max_len=8)
        quote_char = rng.choice(["'", '"'])
        # Build an unclosed quote: echo '<token> or echo "<token>
        tokens = ["echo", f"{quote_char}{token}"]
        payload = _call_rewrite(tokens, capsys)
        assert payload["action"] == "skip"
        assert "unbalanced quotes" in str(payload.get("reason", ""))


def test_bounded_shell_metacharacters_outside_quotes_are_skipped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rng = random.Random(1337)
    operators: list[str] = ["&&", "||", ";", "|", "&", "<", ">"]

    # We construct commands with NO quotes; operators are therefore unambiguously "outside quotes".
    for _ in range(50):
        op = rng.choice(operators)
        left = _rand_token(rng)
        right = _rand_token(rng)
        # "echo a <op> echo b"
        tokens: list[str] = ["echo", left, op, "echo", right]
        payload = _call_rewrite(tokens, capsys)
        assert payload["action"] == "skip"
        assert "shell metacharacters" in str(payload.get("reason", ""))


def test_bounded_heredoc_markers_outside_quotes_are_skipped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rng = random.Random(2024)
    for _ in range(30):
        token = _rand_token(rng, min_len=1, max_len=8)
        # "cat << TOKEN" => heredoc marker outside quotes => skip.
        tokens = ["cat", "<<", token]
        payload = _call_rewrite(tokens, capsys)
        assert payload["action"] == "skip"
        assert "heredoc marker detected" in str(payload.get("reason", ""))


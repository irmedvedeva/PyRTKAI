from __future__ import annotations

import random

from pyrtkai.shell_parse import extract_env_prefix


def _rand_ident(rng: random.Random) -> str:
    first = rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    rest = "".join(
        rng.choice(alphabet) for _ in range(rng.randint(0, 8))
    )
    return first + rest


def _rand_value(rng: random.Random) -> str:
    # Keep it simple: no spaces, no quotes.
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./-"
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 12)))


def _build_cmd(env_pairs: list[str], rest: list[str]) -> str:
    return " ".join(env_pairs + rest)


def test_extract_env_prefix_stops_at_first_non_assignment_bounded() -> None:
    rng = random.Random(424242)

    rest = ["git", "status", "--porcelain"]
    for _ in range(80):
        n = rng.randint(0, 6)
        env_pairs: list[str] = []
        for _ in range(n):
            env_pairs.append(f"{_rand_ident(rng)}={_rand_value(rng)}")

        # Inject a non-assignment token.
        non_assignment = rng.choice(["echo", "status", "X1", "git"])

        cmd = _build_cmd(env_pairs, [non_assignment, *rest])
        env_prefix, cmd_wo_prefix = extract_env_prefix(cmd)

        expected_prefix = " ".join(env_pairs).strip()
        assert env_prefix == expected_prefix
        assert cmd_wo_prefix == _build_cmd([], [non_assignment, *rest]).strip()


def test_extract_env_prefix_with_no_env_prefix_returns_empty_env() -> None:
    env_prefix, cmd_wo_prefix = extract_env_prefix("git status")
    assert env_prefix == ""
    assert cmd_wo_prefix == "git status"


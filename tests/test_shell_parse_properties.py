"""
Bounded property-style checks for shell_parse (no Hypothesis dependency).
Seeded RNG keeps runs deterministic for CI.
"""

from __future__ import annotations

import random
import string

from pyrtkai.shell_parse import (
    extract_env_prefix,
    find_heredoc_marker_outside_quotes,
    has_shell_metacharacters_outside_quotes,
    has_unbalanced_quotes,
    tokenize_shell_like,
)


def _rand_lower(rng: random.Random, lo: int = 1, hi: int = 6) -> str:
    n = rng.randint(lo, hi)
    return "".join(rng.choice(string.ascii_lowercase) for _ in range(n))


def _rand_env_name(rng: random.Random) -> str:
    first = rng.choice(string.ascii_letters + "_")
    rest = "".join(
        rng.choice(string.ascii_letters + string.digits + "_")
        for _ in range(rng.randint(0, 5))
    )
    return first + rest


def _rand_env_value(rng: random.Random) -> str:
    # No whitespace or shell meta — keeps tokenization single-token per assignment.
    alphabet = string.ascii_lowercase + string.digits + "_-."
    n = rng.randint(0, 8)
    return "".join(rng.choice(alphabet) for _ in range(n))


def test_property_safe_words_no_metachar_no_heredoc_no_unbalanced() -> None:
    rng = random.Random(7001)
    meta = set("&|;<>\"'\\")
    for _ in range(120):
        parts = [_rand_lower(rng) for _ in range(rng.randint(1, 12))]
        s = " ".join(parts)
        if any(c in meta for c in s):
            continue
        assert has_shell_metacharacters_outside_quotes(s) is False
        assert find_heredoc_marker_outside_quotes(s) is False
        assert has_unbalanced_quotes(s) is False


def test_property_appending_unquoted_gt_triggers_metachar() -> None:
    rng = random.Random(7002)
    for _ in range(80):
        parts = [_rand_lower(rng) for _ in range(rng.randint(1, 8))]
        base = " ".join(parts)
        s = f"{base} >out"
        assert has_shell_metacharacters_outside_quotes(s) is True


def test_property_tokenize_join_roundtrip_for_safe_tokens() -> None:
    rng = random.Random(7003)
    for _ in range(150):
        tokens = [_rand_lower(rng) for _ in range(rng.randint(0, 10))]
        s = " ".join(tokens)
        assert tokenize_shell_like(s) == tokens


def test_property_extract_env_prefix_splits_assignment_chain() -> None:
    rng = random.Random(7004)
    for _ in range(100):
        k = rng.randint(0, 5)
        env_toks = [f"{_rand_env_name(rng)}={_rand_env_value(rng)}" for _ in range(k)]
        cmd_toks = [_rand_lower(rng), _rand_lower(rng)]
        s = " ".join(env_toks + cmd_toks)
        ep, cmd = extract_env_prefix(s)
        assert ep == " ".join(env_toks).strip()
        assert cmd == " ".join(cmd_toks).strip()


def test_property_double_quoted_segment_hides_metacharacters() -> None:
    rng = random.Random(7005)
    inner_ops = ["&&", "||", ";", "|", ">", "<", "&"]
    for _ in range(60):
        op = rng.choice(inner_ops)
        a = _rand_lower(rng)
        b = _rand_lower(rng)
        s = f'echo "{a}{op}{b}"'
        assert has_shell_metacharacters_outside_quotes(s) is False

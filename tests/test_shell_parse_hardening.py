from __future__ import annotations

import pytest

from pyrtkai.shell_parse import (
    find_heredoc_marker_outside_quotes,
    has_shell_metacharacters_outside_quotes,
    has_unbalanced_quotes,
)


@pytest.mark.parametrize(
    "s,expected",
    [
        ("echo ok", False),
        ("echo 'ok'", False),
        ("echo \"ok\"", False),
        ("echo 'oops", True),
        ("echo \"oops", True),
        (r"echo \"still\" ok", False),
        # Conservative behavior: backslash does not escape the quote inside single quotes.
        (r"echo 'single\\' still'", True),
    ],
)
def test_has_unbalanced_quotes_basic(s: str, expected: bool) -> None:
    assert has_unbalanced_quotes(s) is expected


@pytest.mark.parametrize(
    "s,expected",
    [
        ("cat <<EOF", True),
        ("echo hi<<EOF", True),
        ("echo \"<<EOF\"", False),
        ("echo '<<EOF'", False),
        # Conservative: escaped quotes are not treated as real quoting boundaries.
        (r"echo \"prefix<<EOF suffix\"", True),
        (r"echo 'prefix<<EOF suffix'", False),
    ],
)
def test_heredoc_marker_detection_outside_quotes(s: str, expected: bool) -> None:
    assert find_heredoc_marker_outside_quotes(s) is expected


@pytest.mark.parametrize(
    "s,expected",
    [
        ("echo a && echo b", True),
        ("echo a || echo b", True),
        ("echo a ; echo b", True),
        ("echo a | echo b", True),
        ("echo a & echo b", True),
        ("echo a < file", True),
        ("echo a > file", True),
        ("echo \"a && b\"", False),
        ("echo 'a && b'", False),
        ("echo \"a; b\"", False),
        ("echo 'a|b'", False),
        ("echo \"a<b>c\"", False),
        ("echo 'a<b>c'", False),
        ("echo \"a & b\"", False),
    ],
)
def test_shell_metacharacters_outside_quotes_detection(
    s: str, expected: bool
) -> None:
    assert has_shell_metacharacters_outside_quotes(s) is expected


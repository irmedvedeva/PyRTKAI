from __future__ import annotations

import re

_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")


def has_unbalanced_quotes(s: str) -> bool:
    """
    Minimal unbalanced quote detection.
    - Tracks single and double quotes.
    - Backslash escapes the next char outside single quotes.
    """
    quote: str | None = None
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and quote != "'":
            i += 2
            continue
        if ch in ("'", '"'):
            if quote is None:
                quote = ch
            elif quote == ch:
                quote = None
        i += 1
    return quote is not None


def find_heredoc_marker_outside_quotes(s: str) -> bool:
    """
    Detects `<<` outside quotes. Conservative: if it appears, skip rewriting.
    """
    quote: str | None = None
    i = 0
    while i < len(s) - 1:
        ch = s[i]
        if ch == "\\" and quote != "'":
            i += 2
            continue
        if ch in ("'", '"'):
            if quote is None:
                quote = ch
            elif quote == ch:
                quote = None
            i += 1
            continue
        if quote is None and s[i : i + 2] == "<<":
            return True
        i += 1
    return False


def has_shell_metacharacters_outside_quotes(s: str) -> bool:
    """
    Conservative detection of shell metacharacters that our MVP proxy cannot execute
    correctly without a shell (no shell=True in subprocess).
    Returns True if any of the following appear outside quotes:
      - compound operators: &&, ||
      - separators/background: ;, |, &
      - redirections: <, >
    """
    quote: str | None = None
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and quote != "'":
            i += 2
            continue

        if ch in ("'", '"'):
            if quote is None:
                quote = ch
            elif quote == ch:
                quote = None
            i += 1
            continue

        if quote is None:
            if s[i : i + 2] in {"&&", "||"}:
                return True
            if ch in {";", "|", "&", "<", ">"}:
                return True
        i += 1
    return False


def tokenize_shell_like(s: str) -> list[str]:
    """
    Simple whitespace tokenizer respecting quotes.
    Intended for env-prefix extraction only.
    """
    tokens: list[str] = []
    cur: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and quote != "'":
            if i + 1 < len(s):
                cur.append(s[i + 1])
                i += 2
                continue
        if ch in ("'", '"'):
            if quote is None:
                quote = ch
            elif quote == ch:
                quote = None
            cur.append(ch)
            i += 1
            continue
        if quote is None and ch.isspace():
            if cur:
                tokens.append("".join(cur))
                cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1

    if cur:
        tokens.append("".join(cur))
    return tokens


def extract_env_prefix(cmd_str: str) -> tuple[str, str]:
    """
    Extracts a leading env-prefix consisting of consecutive NAME=VALUE tokens.
    Returns (env_prefix, command_without_prefix).
    Conservative: stops at the first non-assignment token.
    """
    tokens = tokenize_shell_like(cmd_str)
    env_tokens: list[str] = []
    rest_tokens: list[str] = []

    it = iter(tokens)
    for tok in it:
        if _ASSIGNMENT_RE.match(tok):
            env_tokens.append(tok)
        else:
            rest_tokens.append(tok)
            rest_tokens.extend(list(it))
            break

    env_prefix = " ".join(env_tokens).strip()
    cmd = " ".join(rest_tokens).strip()
    return env_prefix, cmd


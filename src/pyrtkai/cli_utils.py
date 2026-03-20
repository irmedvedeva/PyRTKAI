"""Shared helpers for CLI subcommands."""


def sanitize_sqlite_limit(limit: int) -> int:
    # Security/robustness: SQLite `LIMIT -1` means "no limit".
    return limit if limit >= 0 else 0

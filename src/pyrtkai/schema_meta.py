from __future__ import annotations

from typing import Final

SCHEMA_VERSION: Final[int] = 1

SCHEMA_DOCTOR: Final[str] = "doctor"
SCHEMA_STATUS: Final[str] = "status"
SCHEMA_GAIN_SUMMARY: Final[str] = "gain_summary"
SCHEMA_GAIN_PROJECT_SUMMARY: Final[str] = "gain_project_summary"

_KNOWN_SCHEMAS: Final[set[str]] = {
    SCHEMA_DOCTOR,
    SCHEMA_STATUS,
    SCHEMA_GAIN_SUMMARY,
    SCHEMA_GAIN_PROJECT_SUMMARY,
}


def build_schema_meta(schema: str) -> dict[str, object]:
    """
    Build a stable `_meta` object for machine-readable JSON payloads.
    """
    if schema not in _KNOWN_SCHEMAS:
        raise ValueError(f"unknown schema id: {schema!r}")
    return {
        "schema": schema,
        "schema_version": SCHEMA_VERSION,
    }


def attach_schema_meta(payload: dict[str, object], *, schema: str) -> dict[str, object]:
    """
    Return a shallow copy with additive `_meta` fields.
    """
    out = dict(payload)
    out["_meta"] = build_schema_meta(schema)
    return out

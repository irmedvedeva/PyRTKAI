from __future__ import annotations

import pytest

from pyrtkai.schema_meta import (
    SCHEMA_DOCTOR,
    SCHEMA_GAIN_PROJECT_SUMMARY,
    SCHEMA_GAIN_SUMMARY,
    SCHEMA_STATUS,
    SCHEMA_VERSION,
    attach_schema_meta,
    build_schema_meta,
)


def test_build_schema_meta_known_schemas() -> None:
    for schema in (
        SCHEMA_DOCTOR,
        SCHEMA_STATUS,
        SCHEMA_GAIN_SUMMARY,
        SCHEMA_GAIN_PROJECT_SUMMARY,
    ):
        meta = build_schema_meta(schema)
        assert meta["schema"] == schema
        assert meta["schema_version"] == SCHEMA_VERSION


def test_build_schema_meta_rejects_unknown_schema() -> None:
    with pytest.raises(ValueError, match="unknown schema id"):
        build_schema_meta("unknown_schema")


def test_attach_schema_meta_is_additive() -> None:
    payload = {"k": "v"}
    out = attach_schema_meta(payload, schema=SCHEMA_STATUS)
    assert out["k"] == "v"
    assert out["_meta"]["schema"] == SCHEMA_STATUS
    assert payload == {"k": "v"}

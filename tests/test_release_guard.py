from __future__ import annotations

import pytest

from pyrtkai.release_guard import parse_release_tag, validate_release_tag_alignment


def test_parse_release_tag_strict_semver_only() -> None:
    assert parse_release_tag("v0.1.2") == "0.1.2"
    assert parse_release_tag("v10.20.30") == "10.20.30"
    assert parse_release_tag("0.1.2") is None
    assert parse_release_tag("v0.1") is None
    assert parse_release_tag("v0.1.2-rc1") is None


def test_validate_release_tag_alignment_ignored_for_non_release_event() -> None:
    validate_release_tag_alignment(
        package_version="0.1.2",
        event_name="workflow_dispatch",
        ref_name="v9.9.9",
    )


def test_validate_release_tag_alignment_accepts_matching_release() -> None:
    validate_release_tag_alignment(
        package_version="0.1.2",
        event_name="release",
        ref_name="v0.1.2",
    )


def test_validate_release_tag_alignment_rejects_bad_tag_format() -> None:
    with pytest.raises(ValueError, match="vX.Y.Z"):
        validate_release_tag_alignment(
            package_version="0.1.2",
            event_name="release",
            ref_name="release-0.1.2",
        )


def test_validate_release_tag_alignment_rejects_mismatch() -> None:
    with pytest.raises(ValueError, match="mismatch"):
        validate_release_tag_alignment(
            package_version="0.1.2",
            event_name="release",
            ref_name="v0.1.3",
        )

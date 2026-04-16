from __future__ import annotations

import re

_SEMVER_TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def parse_release_tag(tag: str) -> str | None:
    """
    Return version string from a strict release tag (vX.Y.Z), else None.
    """
    m = _SEMVER_TAG_RE.fullmatch(tag.strip())
    if m is None:
        return None
    return f"{m.group(1)}.{m.group(2)}.{m.group(3)}"


def validate_release_tag_alignment(
    *,
    package_version: str,
    event_name: str,
    ref_name: str,
) -> None:
    """
    Fail fast for release publishes when tag and package version diverge.

    Policy:
    - Only enforced for `release` events.
    - Tag format must be strict `vX.Y.Z`.
    - Parsed tag version must equal `pyrtkai.__version__`.
    """
    if event_name != "release":
        return

    parsed = parse_release_tag(ref_name)
    if parsed is None:
        raise ValueError(
            f"release tag must match vX.Y.Z (got {ref_name!r}); "
            "refuse publish to avoid version drift"
        )
    if parsed != package_version:
        raise ValueError(
            f"release tag/version mismatch: tag={ref_name!r} -> {parsed!r}, "
            f"package __version__={package_version!r}"
        )

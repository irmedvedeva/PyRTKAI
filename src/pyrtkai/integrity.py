from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HookIntegrityResult:
    ok: bool
    expected: str | None
    actual: str | None
    reason: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 256), b""):
            h.update(chunk)
    return h.hexdigest()


def store_sha256_baseline(hook_path: Path, baseline_path: Path) -> None:
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    expected = sha256_file(hook_path)
    # Single-line format: "<hex>\n"
    baseline_path.write_text(expected + "\n", encoding="utf-8")


def load_baseline_sha256(baseline_path: Path) -> str | None:
    if not baseline_path.exists():
        return None
    txt = baseline_path.read_text(encoding="utf-8").strip()
    if len(txt) != 64:
        return None
    # Defensive: accept only hex.
    try:
        int(txt, 16)
    except ValueError:
        return None
    return txt


def verify_sha256_baseline(
    hook_path: Path,
    baseline_path: Path,
) -> HookIntegrityResult:
    actual: str | None
    expected = load_baseline_sha256(baseline_path)
    if expected is None:
        return HookIntegrityResult(
            ok=False,
            expected=None,
            actual=None,
            reason="missing_or_invalid_baseline",
        )
    if not hook_path.exists():
        return HookIntegrityResult(
            ok=False,
            expected=expected,
            actual=None,
            reason="hook_missing",
        )

    actual = sha256_file(hook_path)
    ok = actual == expected
    return HookIntegrityResult(
        ok=ok,
        expected=expected,
        actual=actual,
        reason="verified" if ok else "tampered",
    )


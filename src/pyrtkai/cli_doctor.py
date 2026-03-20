from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from pyrtkai.cursor_hooks_discover import (
    baseline_path_for_hook,
    hooks_json_configured_for_pyrtkai,
    parse_hooks_json_dict,
    pick_hook_path_for_integrity,
)
from pyrtkai.integrity import verify_sha256_baseline
from pyrtkai.output_filter import load_output_filter_config, load_output_filter_profile
from pyrtkai.registry import get_mvp_rewrite_rules_enabled

# Local health check only: avoid loading an unexpectedly huge hooks.json into memory.
_HOOKS_JSON_MAX_BYTES = 1024 * 1024


def _read_hooks_json_text(path: Path) -> str | None:
    try:
        st = path.stat()
    except OSError:
        return None
    if st.st_size > _HOOKS_JSON_MAX_BYTES:
        return None
    return path.read_text(encoding="utf-8")


def run_doctor(args: Namespace) -> int:
    default_hook_path = Path.home() / ".cursor" / "hooks" / "pyrtkai-rewrite.sh"

    hooks_json_path = Path.home() / ".cursor" / "hooks.json"
    hooks_json_present = hooks_json_path.exists()
    hooks_json_configured = False
    hooks_root: dict[str, object] | None = None
    if hooks_json_present:
        try:
            hooks_json_text = _read_hooks_json_text(hooks_json_path)
            if hooks_json_text is None:
                hooks_json_configured = False
            else:
                hooks_root = parse_hooks_json_dict(hooks_json_text)
                if hooks_root is None:
                    hooks_json_configured = False
                else:
                    hooks_json_configured = hooks_json_configured_for_pyrtkai(hooks_root)
        except Exception:
            hooks_json_configured = False
            hooks_root = None

    hook_path = (
        pick_hook_path_for_integrity(
            hooks_root if hooks_root is not None else {},
            hooks_json_path,
            default_hook_path,
        )
        if hooks_root is not None
        else default_hook_path
    )
    baseline_path = baseline_path_for_hook(hook_path)
    integrity = verify_sha256_baseline(
        hook_path=hook_path,
        baseline_path=baseline_path,
    )

    max_chars, _trunc_marker = load_output_filter_config()
    profile = load_output_filter_profile()
    payload: dict[str, object] = {
        "hook_integrity": {
            "ok": integrity.ok,
            "reason": integrity.reason,
            "hook_path": str(hook_path),
            "baseline_path": str(baseline_path),
        },
        "hooks_json": {
            "present": hooks_json_present,
            "configured": hooks_json_configured,
        },
        "mvp_rewrite_rules": get_mvp_rewrite_rules_enabled(),
        "output_filter": {
            "profile": profile,
            "max_chars": max_chars,
        },
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        ok = bool(integrity.ok and hooks_json_configured)
        print(
            f"ok={ok} hook_integrity_ok={integrity.ok} "
            f"hooks_json_configured={hooks_json_configured}"
        )

    return 0 if integrity.ok and hooks_json_configured else 1

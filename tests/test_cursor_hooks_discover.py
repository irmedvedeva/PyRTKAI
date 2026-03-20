from __future__ import annotations

from pathlib import Path

import pytest

from pyrtkai.cursor_hooks_discover import (
    hooks_json_configured_for_pyrtkai,
    matcher_covers_shell,
    pick_hook_path_for_integrity,
    resolve_hook_command_path,
)


def test_matcher_covers_shell() -> None:
    assert matcher_covers_shell("Shell") is True
    assert matcher_covers_shell("Read|Shell|Write") is True
    assert matcher_covers_shell("Read") is False
    assert matcher_covers_shell("") is False


def test_resolve_hook_command_relative(tmp_path: Path) -> None:
    parent = tmp_path / ".cursor"
    scripts = parent / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "pyrtkai-rewrite.sh"
    script.write_text("#!/bin/sh\necho\n", encoding="utf-8")
    resolved = resolve_hook_command_path("./scripts/pyrtkai-rewrite.sh", parent)
    assert resolved == script.resolve()


@pytest.mark.parametrize(
    ("hooks", "expected"),
    [
        (
            {
                "hooks": {
                    "preToolUse": [
                        {"command": "./hooks/pyrtkai-rewrite.sh", "matcher": "Shell"}
                    ]
                }
            },
            True,
        ),
        (
            {
                "hooks": {
                    "beforeShellExecution": [
                        {"command": "/opt/plugin/scripts/pyrtkai-rewrite.sh"}
                    ]
                }
            },
            True,
        ),
        (
            {"hooks": {"preToolUse": [{"command": "./hooks/other.sh", "matcher": "Shell"}]}},
            False,
        ),
    ],
)
def test_hooks_json_configured_for_pyrtkai(hooks: dict[str, object], expected: bool) -> None:
    assert hooks_json_configured_for_pyrtkai(hooks) is expected


def test_pick_hook_path_prefers_resolved_file(tmp_path: Path) -> None:
    parent = tmp_path / ".cursor"
    scripts = parent / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "pyrtkai-rewrite.sh"
    script.write_text("#!/bin/sh\necho\n", encoding="utf-8")
    hooks_json = parent / "hooks.json"
    root = {
        "hooks": {
            "preToolUse": [
                {"command": "./scripts/pyrtkai-rewrite.sh", "matcher": "Shell"}
            ]
        }
    }
    default = parent / "hooks" / "pyrtkai-rewrite.sh"
    chosen = pick_hook_path_for_integrity(root, hooks_json, default)
    assert chosen == script.resolve()

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from pyrtkai.integrity import load_baseline_sha256, sha256_file


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _cursor_plugin_root() -> Path:
    return _repo_root() / "integrations" / "cursor-plugin"


def _collect_json_strings(obj: object, out: list[str]) -> None:
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_json_strings(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_json_strings(item, out)


def test_plugin_manifest_and_hooks_parse() -> None:
    root = _cursor_plugin_root()
    manifest = root / ".cursor-plugin" / "plugin.json"
    hooks = root / "hooks" / "hooks.json"
    assert manifest.is_file()
    assert hooks.is_file()
    m = json.loads(manifest.read_text(encoding="utf-8"))
    h = json.loads(hooks.read_text(encoding="utf-8"))
    assert m.get("name") == "pyrtkai"
    assert isinstance(m.get("hooks"), str)
    assert "hooks" in h
    logo_rel = m.get("logo")
    assert isinstance(logo_rel, str) and not logo_rel.startswith("..")
    logo_path = (root / logo_rel).resolve()
    assert logo_path.is_file()
    assert root.resolve() in logo_path.parents or logo_path.parent == root.resolve()


def test_plugin_paths_no_parent_traversal() -> None:
    root = _cursor_plugin_root()
    strings: list[str] = []
    for path in (
        root / ".cursor-plugin" / "plugin.json",
        root / "hooks" / "hooks.json",
    ):
        _collect_json_strings(json.loads(path.read_text(encoding="utf-8")), strings)
    for s in strings:
        if ".." in s:
            raise AssertionError(f"suspicious path segment in JSON string: {s!r}")


def test_bundled_hook_sha256_matches_baseline() -> None:
    root = _cursor_plugin_root()
    script = root / "scripts" / "pyrtkai-rewrite.sh"
    baseline = root / "scripts" / ".pyrtkai-rewrite.sh.sha256"
    assert script.is_file()
    assert baseline.is_file()
    expected = load_baseline_sha256(baseline)
    assert expected is not None
    assert sha256_file(script) == expected


def test_bundled_hook_script_invokes_pyrtkai() -> None:
    """Smoke: repo script + stdin JSON produces valid hook stdout (uses same Python as pytest)."""
    import subprocess

    root = _cursor_plugin_root()
    script = root / "scripts" / "pyrtkai-rewrite.sh"
    payload = json.dumps({"tool_input": {"command": "echo hi"}})
    env = {**os.environ, "PYRTKAI_PYTHON": sys.executable}
    result = subprocess.run(
        ["bash", str(script)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=env,
    )
    assert result.returncode == 0, (result.stderr, result.stdout)
    out = json.loads(result.stdout.strip())
    assert isinstance(out, dict)


def test_bundled_hook_script_uses_exec_double_dash_for_python_path() -> None:
    """Hardening: PYRTKAI_PYTHON execution path must terminate option parsing."""
    root = _cursor_plugin_root()
    script = root / "scripts" / "pyrtkai-rewrite.sh"
    text = script.read_text(encoding="utf-8")
    assert 'exec -- "$PYRTKAI_PYTHON" -m pyrtkai.cli hook' in text

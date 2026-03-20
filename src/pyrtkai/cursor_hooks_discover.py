from __future__ import annotations

import json
import shlex
from pathlib import Path


def matcher_covers_shell(matcher: object) -> bool:
    """True if a preToolUse matcher string includes the Shell tool."""
    if not isinstance(matcher, str) or not matcher.strip():
        return False
    parts = [p.strip() for p in matcher.split("|") if p.strip()]
    return "Shell" in parts


def _first_token(command: str) -> str | None:
    try:
        parts = shlex.split(command.strip(), posix=True)
    except ValueError:
        return None
    if not parts:
        return None
    return parts[0]


def resolve_hook_command_path(token: str, hooks_json_parent: Path) -> Path | None:
    """
    Resolve the hook script path the same way as typical ~/.cursor/hooks.json layouts:
    - Absolute path: use as-is if the file exists.
    - Relative path: resolve under hooks_json_parent (usually ~/.cursor).
    """
    raw = Path(token)
    if raw.is_absolute():
        return raw if raw.is_file() else None
    candidate = (hooks_json_parent / raw).resolve()
    return candidate if candidate.is_file() else None


def hooks_json_configured_for_pyrtkai(hooks_root: object) -> bool:
    """True if hooks.json wires a Shell (or beforeShellExecution) hook to pyrtkai-rewrite.sh."""
    if not isinstance(hooks_root, dict):
        return False
    hooks = hooks_root.get("hooks")
    if not isinstance(hooks, dict):
        return False

    for entry in hooks.get("preToolUse", []):
        if not isinstance(entry, dict):
            continue
        if not matcher_covers_shell(entry.get("matcher")):
            continue
        cmd = entry.get("command")
        if not isinstance(cmd, str):
            continue
        token = _first_token(cmd)
        if token and Path(token).name == "pyrtkai-rewrite.sh":
            return True

    for entry in hooks.get("beforeShellExecution", []):
        if not isinstance(entry, dict):
            continue
        cmd = entry.get("command")
        if not isinstance(cmd, str):
            continue
        token = _first_token(cmd)
        if token and Path(token).name == "pyrtkai-rewrite.sh":
            return True

    return False


def pick_hook_path_for_integrity(
    hooks_root: object,
    hooks_json_path: Path,
    default_hook_path: Path,
) -> Path:
    """
    Prefer a path discovered from hooks.json that exists on disk; otherwise default_hook_path.
    """
    if not isinstance(hooks_root, dict):
        return default_hook_path
    hooks = hooks_root.get("hooks")
    if not isinstance(hooks, dict):
        return default_hook_path

    parent = hooks_json_path.parent
    candidates: list[Path] = []

    def collect_from_pre(entries: object) -> None:
        if not isinstance(entries, list):
            return
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if not matcher_covers_shell(entry.get("matcher")):
                continue
            cmd = entry.get("command")
            if not isinstance(cmd, str):
                continue
            token = _first_token(cmd)
            if not token or Path(token).name != "pyrtkai-rewrite.sh":
                continue
            resolved = resolve_hook_command_path(token, parent)
            if resolved is not None:
                candidates.append(resolved)

    def collect_from_shell(entries: object) -> None:
        if not isinstance(entries, list):
            return
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            cmd = entry.get("command")
            if not isinstance(cmd, str):
                continue
            token = _first_token(cmd)
            if not token or Path(token).name != "pyrtkai-rewrite.sh":
                continue
            resolved = resolve_hook_command_path(token, parent)
            if resolved is not None:
                candidates.append(resolved)

    collect_from_pre(hooks.get("preToolUse", []))
    collect_from_shell(hooks.get("beforeShellExecution", []))

    for p in candidates:
        if p.is_file():
            return p

    return default_hook_path


def baseline_path_for_hook(hook_path: Path) -> Path:
    return hook_path.parent / ".pyrtkai-rewrite.sh.sha256"


def parse_hooks_json_dict(text: str) -> dict[str, object] | None:
    try:
        root = json.loads(text)
    except json.JSONDecodeError:
        return None
    return root if isinstance(root, dict) else None

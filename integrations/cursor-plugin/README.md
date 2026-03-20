# PyRTKAI — Cursor plugin (bundle)

This directory is a **Cursor Marketplace–shaped** plugin layout: manifest, hooks, and the shell wrapper that invokes `pyrtkai hook`.

## Quick start (before first Cursor session)

1. Clone this repository and create a venv **in the repo root** (PyPI package **not** published yet):

   ```bash
   cd /path/to/PyRTKAI
   python3 -m venv .venv
   .venv/bin/pip install -U pip
   .venv/bin/pip install -e .
   ```

2. Expose the same interpreter to **Cursor** (hooks do not inherit your shell unless configured):

   ```bash
   export PYRTKAI_PYTHON="/path/to/PyRTKAI/.venv/bin/python"
   ```

   Use an **absolute path**. Only set this to a **Python binary you trust** (same rule as `PATH`).

3. Merge `hooks/hooks.json` into `~/.cursor/hooks.json` and install/copy `scripts/pyrtkai-rewrite.sh` to the path your `command` references (see **Manual install**).

4. Run **`pyrtkai doctor --json`** — expect `hooks_json.configured` and `hook_integrity.ok` when paths match.

If `pyrtkai` is missing, the hook script exits with an error (no silent failure). Install **before** relying on the agent.

## Windows

The wrapper is **`bash`**. On Windows use **Git Bash**, **WSL**, or another environment where `bash` runs and `PYRTKAI_PYTHON` points at your venv’s `python.exe` / `python` as appropriate. Native `cmd.exe`-only setups are unsupported for this shell hook.

## Prerequisites (details)

1. **Python 3.11+** and **`pyrtkai` installed** from this repository (**not on PyPI yet** — `pip install pyrtkai` will fail until published).

   **Recommended:** venv **inside the clone**, editable install (same flow as day-to-day development):

   ```bash
   cd /path/to/PyRTKAI
   python3 -m venv .venv
   .venv/bin/pip install -U pip
   .venv/bin/pip install -e .
   ```

   Point the Cursor hook at that interpreter (absolute path is most reliable):

   ```bash
   export PYRTKAI_PYTHON="/path/to/PyRTKAI/.venv/bin/python"
   ```

   (Set `PYRTKAI_PYTHON` in the environment Cursor inherits, e.g. your shell profile or desktop session, so agent hooks see it.)

   **Alternative:** a separate venv, e.g. `python3 -m venv ~/.venvs/pyrtkai` then `~/.venvs/pyrtkai/bin/pip install -e /path/to/PyRTKAI` and `PYRTKAI_PYTHON=$HOME/.venvs/pyrtkai/bin/python`.

   **PEP 668 (e.g. Debian/Ubuntu):** do not use system `pip` without a venv; the commands above avoid `externally-managed-environment`.

   **After a PyPI release:** `pip install pyrtkai` inside any venv will be enough; still set `PYRTKAI_PYTHON` if `pyrtkai` is not on the default `PATH` Cursor uses.

2. The hook script uses, in order:
   - **`PYRTKAI_PYTHON`** (full path to `python`) if set — useful when multiple Python installs exist;
   - else **`pyrtkai`** on `PATH`;
   - else **`python3 -m pyrtkai.cli hook`**.

Without a working interpreter + install, the hook will fail when Cursor runs it.

## Layout

| Path | Role |
|------|------|
| `.cursor-plugin/plugin.json` | Plugin manifest (submit the **repository** that contains this tree to [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish)). |
| `.cursor-plugin/plugin.repository.fragment.json` | Merge **`repository`** + **`homepage`** into `plugin.json` when the repo is public (replace `YOUR_ORG`). |
| `hooks/hooks.json` | Registers `preToolUse` + `Shell` matcher → `./scripts/pyrtkai-rewrite.sh`. |
| `scripts/pyrtkai-rewrite.sh` | Forwards stdin/stdout to `pyrtkai hook`. |
| `scripts/.pyrtkai-rewrite.sh.sha256` | Expected SHA-256 of `pyrtkai-rewrite.sh` (used by tests and optional `verify-hook`). |
| `assets/logo.png` | Marketplace listing logo (RTK branding). |

## Manual install (without Marketplace)

Copy or symlink into your Cursor config (paths vary by OS):

- Install the wrapper and baseline under `~/.cursor/hooks/` **or** keep paths consistent with your `~/.cursor/hooks.json` `command` field.
- Merge `hooks/hooks.json` entries into your existing `~/.cursor/hooks.json` if you already use hooks.

Then run:

```bash
pyrtkai doctor --json
```

`doctor` detects `preToolUse` / `beforeShellExecution` entries whose command resolves to `pyrtkai-rewrite.sh` and verifies integrity against `.pyrtkai-rewrite.sh.sha256` next to that script when present.

## Marketplace submission

Before publishing: merge keys from **`plugin.repository.fragment.json`** into **`plugin.json`** (public Git URL). Root **`LICENSE`** (MIT) and **`SECURITY.md`** should be present for reviewer expectations. See **`PRE_PUBLISH_CHECKLIST.ru.md`** (Russian) or the [official checklist](https://cursor.com/docs/reference/plugins).

## E2E (human)

On a clean machine: install the plugin from Git (or copy this tree), install `pyrtkai`, open Cursor, trigger an agent **Shell** tool call, and confirm `doctor --json` reports `hooks_json.configured` and `hook_integrity.ok`.

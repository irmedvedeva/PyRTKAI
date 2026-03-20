#!/usr/bin/env bash
set -euo pipefail
# PyRTKAI Cursor hook: read hook JSON from stdin, write hook JSON to stdout.
# Requires: pyrtkai (prefer: repo .venv + pip install -e .; or pip install pyrtkai once on PyPI).
# Optional: PYRTKAI_PYTHON=/path/to/python to force the interpreter (multi-venv / CI).
if [ -n "${PYRTKAI_PYTHON:-}" ]; then
  exec "$PYRTKAI_PYTHON" -m pyrtkai.cli hook
fi
if command -v pyrtkai >/dev/null 2>&1; then
  exec pyrtkai hook
fi
exec python3 -m pyrtkai.cli hook

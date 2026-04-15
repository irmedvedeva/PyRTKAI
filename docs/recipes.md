# Recipes (Cursor / agent terminal workflows)

Short, copy-paste patterns. Env vars: [environment-variables.md](environment-variables.md). Safety: [SECURITY.md](../SECURITY.md).

## 1. Shrink noisy command output

Use when a command prints far more text than the model needs.

```bash
export PYRTKAI_OUTPUT_MAX_CHARS=8000
pyrtkai proxy --summary -- your-command --your-args
```

Tune `PYRTKAI_OUTPUT_MAX_CHARS` and optionally `PYRTKAI_TRUNC_MARKER`. JSON-shaped stdout is passed through when detected.

## 2. Fail-closed deny for dangerous patterns

Block commands matching a regex at the hook layer (in addition to IDE rules).

```bash
export PYRTKAI_DENY_REGEXES='rm -rf /,mkfs'
printf '%s' '{"hookEventName":"PreToolUse","tool_input":{"command":"echo ok"}}' | pyrtkai hook
```

Invalid regex in env → deny (fail-closed). See [workflows-and-positioning.md](workflows-and-positioning.md) for how each hook shape responds.

## 3. Preserve tool JSON

Run tools that emit a single JSON object (or NDJSON) through `proxy` without naive truncation breaking parsers:

```bash
pyrtkai proxy python3 -c "import json; print(json.dumps({'ok': True, 'n': 42}))"
```

## 4. After installing the Cursor bundle

Point `PYRTKAI_PYTHON` at the venv interpreter, merge `hooks.json` per [integrations/cursor-plugin/README.md](../integrations/cursor-plugin/README.md), then:

```bash
pyrtkai verify-hook --json
pyrtkai doctor --json
```

## 5. Optional local savings metrics

Enable SQLite-backed events (see env docs), then:

```bash
export PYRTKAI_GAIN_ENABLED=1
pyrtkai proxy --summary -- python3 -c "print('x' * 5000)"
pyrtkai status --json
```

## Related

- [Workflows & positioning](workflows-and-positioning.md) — same-command benchmark snippet.
- `pyrtkai init --quickstart` — guided first run.

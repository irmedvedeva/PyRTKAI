# Workflows & positioning (short guide)

This page is a **one-screen** complement to [README.md](../README.md) and [SECURITY.md](../SECURITY.md): *what PyRTKAI is for*, *how it differs from a raw agent shell*, and *how hook behavior varies by host*.

## What PyRTKAI adds on top of a normal terminal

| Aspect | Unwrapped agent / shell | With PyRTKAI |
|--------|-------------------------|--------------|
| Child process execution | Often shell-invoked or opaque to tooling | **`proxy`** runs the program with **argv-only** `subprocess` (no shell) |
| Huge command output | Full stream may flood context | Deterministic **text truncation** + marker; **JSON / NDJSON pass-through** when detected |
| Local policy | IDE lists only | Optional **`PYRTKAI_DENY_REGEXES`** at the hook layer; invalid config → **deny** (fail-closed) |
| Metrics | None by default | Optional **`gain`** (local SQLite) + **`proxy --summary`** (stderr heuristic) |

PyRTKAI is **not** a hosted “run any shell for me” product: it optimizes **predictable, inspectable** execution and output shaping.

## Same command: see truncation and a savings line

Use the **same** inner command twice; only the second run goes through `proxy` with a low char cap and **`--summary`**.

```bash
export PYRTKAI_OUTPUT_MAX_CHARS=120
# Baseline: full (or very long) output
python3 -c "print('x' * 400)"
# Through proxy: truncated stdout + one stderr line from --summary
pyrtkai proxy --summary -- python3 -c "print('x' * 400)"
```

Expect the second run to show **`[TRUNCATED]`** (or your custom marker) and a **`[pyrtkai]`** line with char/token **estimates** (heuristic, not a model tokenizer).

## Hook adapters: “blocked” and **`explain`**

When **`pyrtkai hook`** returns JSON, some hosts get an explicit **deny** with **`permissionDecisionReason`** and, where applicable, an **`explain`** object (`code`, `why`, `remediation`). Others **pass through** an empty object **`{}`** so the **IDE/agent** keeps authority — see [SECURITY.md](../SECURITY.md) (host vs hook).

Summary (simplified; see `handle_hook_json` in source for exact branches):

| Detected shape | Policy **deny** | Rewrite allowed + policy **allow** | Otherwise (no rewrite / skip) |
|----------------|-----------------|-----------------------------------|------------------------------|
| Cursor-like (`tool_input.command`, no `hookEventName`) | **`{}`** | **`permission` + `updated_input`** with wrapped command | **`{}`** |
| Gemini CLI (`run_shell_command`) | **`{}`** | **`decision` + `hookSpecificOutput`** | **`{"decision": "allow"}`** |
| Copilot CLI (`toolName` bash) | **`permissionDecision` deny** + optional **`explain`** | **`permissionDecision` deny** with token-savings reason (suggested command) | **`{}`** |
| Claude / VS Code–like (`hookEventName` + `tool_input`) | **`hookSpecificOutput`** with deny + **`explain`** | **`hookSpecificOutput`** allow + rewritten command | **`{}`** |

**Consistency:** wherever the payload includes both a human **`permissionDecisionReason`** (or equivalent) and **`explain`**, the **`explain.code`** is stable for automation (e.g. `policy_regex`, `hook_invalid_json`).

Invalid stdin JSON or non-object root uses a **Claude-shaped** fail-closed deny with **`explain`** (`hook_invalid_json`, `hook_payload_not_object`).

## Related

- [Environment variables](environment-variables.md) — `PYRTKAI_*` reference.
- [Product roadmap](product-roadmap.md) — planned steps and deferred scope.

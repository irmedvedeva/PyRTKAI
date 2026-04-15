# Environment variables reference

All variables are **optional** unless noted. PyRTKAI reads them from the process environment of **`pyrtkai`** (and from the interpreter used for `python -m pyrtkai.cli`).

## Hook / IDE (not read by Python code)

| Variable | Purpose |
|----------|---------|
| **`PYRTKAI_PYTHON`** | Absolute path to the **`python`** binary that should run `pyrtkai` from **Cursor** shell hooks (see `integrations/cursor-plugin/`). If unset, wrappers fall back to `pyrtkai` on `PATH` or `python3 -m pyrtkai.cli`. |

## Hook input safety cap

| Variable | Default | Effect |
|----------|---------|--------|
| `PYRTKAI_HOOK_MAX_STDIN_BYTES` | `1048576` | Max bytes read by `pyrtkai hook` from stdin. If exceeded, returns fail-closed deny with `explain.code = hook_input_too_large`. |

## MVP rewrite rules (registry)

Disable a rule with `0`, `false`, `no`, or `off`. Omitted → enabled (defaults below).

| Variable | Default | Effect |
|----------|---------|--------|
| `PYRTKAI_MVP_ENABLE_GIT_STATUS` | enabled | Allow MVP rewrite for `git status`-style commands. |
| `PYRTKAI_MVP_ENABLE_GIT_LOG` | enabled | Allow MVP rewrite for a conservative `git log` subset (blocked when `--json` / `--template` / `--format` is present). |
| `PYRTKAI_MVP_ENABLE_LS` | enabled | `ls` |
| `PYRTKAI_MVP_ENABLE_GREP` | enabled | `grep` |
| `PYRTKAI_MVP_ENABLE_RG` | enabled | `rg` |

### Explicitly disable rewrite rules

If you want raw execution for a specific command class, disable only that rule:

```bash
export PYRTKAI_MVP_ENABLE_GIT_STATUS=0
export PYRTKAI_MVP_ENABLE_GIT_LOG=0
export PYRTKAI_MVP_ENABLE_LS=0
export PYRTKAI_MVP_ENABLE_GREP=0
export PYRTKAI_MVP_ENABLE_RG=0
```

`pyrtkai rewrite` now includes `rewrite_rule_id` and `suggested_disable_env` on rewrite paths so users can copy the exact opt-out toggle for the matched rule.

## Output filter (proxy)

| Variable | Default | Effect |
|----------|---------|--------|
| `PYRTKAI_OUTPUT_MAX_CHARS` | `4000` | Max characters written per stream after filtering (non-JSON text). |
| `PYRTKAI_TRUNC_MARKER` | `\n...[TRUNCATED]...\n` | Marker between head and tail when truncating. |
| `PYRTKAI_OUTPUT_FILTER_PROFILE` | `truncating` | Filter profile name (MVP: truncating). |
| `PYRTKAI_PROXY_SUMMARY` | off | If `1` / `true` / `yes`, after each `pyrtkai proxy` run print a **one-line** heuristic savings summary to **stderr** (same idea as `proxy --summary`). |

## Policy gate (deny regexes)

| Variable | Default | Effect |
|----------|---------|--------|
| `PYRTKAI_DENY_REGEXES` | — | Comma-separated regex patterns; if any matches the command string, **deny** (fail-closed). |
| `PYRTKAI_DENY_REGEX` | — | Single regex alternative to `PYRTKAI_DENY_REGEXES`. |
| `PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS` | `65536` | If the command string is longer than this while deny patterns are set, deny without running regex (fail-closed). |

## Gain tracking (local SQLite)

| Variable | Default | Effect |
|----------|---------|--------|
| `PYRTKAI_GAIN_ENABLED` | off | Set to `1`, `true`, or `yes` to record **`pyrtkai proxy`** runs. |
| `PYRTKAI_GAIN_DB_PATH` | `~/.pyrtkai/gain.sqlite` | SQLite database path. |
| `PYRTKAI_GAIN_RETENTION_DAYS` | `30` | Delete older proxy events when recording (retention cleanup). |
| `PYRTKAI_CHARS_PER_TOKEN` | `4` | Characters per estimated “token” in summaries (heuristic, not a model tokenizer). |

### When `gain summary` shows non-zero savings

Recorded events compare **characters before vs after** filtering per stream. **`tokens_saved_est`** / **`tokens_saved_pct_est`** are **non-zero** when:

- at least one **`pyrtkai proxy`** run was recorded with **`PYRTKAI_GAIN_ENABLED=1`**, and  
- the wrapped command produced **non-JSON text** on stdout or stderr **longer than** `PYRTKAI_OUTPUT_MAX_CHARS`, so the filter **shrinks** output (head + marker + tail).

If output is **JSON/NDJSON pass-through** or shorter than the limit, savings for that run may be **zero** even though `proxy` ran successfully.

## Tests / development only

| Variable | Effect |
|----------|--------|
| `PYRTKAI_ENFORCE_PERF_SLO` | Set to `1` to enforce optional performance bounds in `tests/test_performance_slo.py`. |

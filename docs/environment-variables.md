# Environment variables reference

All variables are **optional** unless noted. PyRTKAI reads them from the process environment of **`pyrtkai`** (and from the interpreter used for `python -m pyrtkai.cli`).

## Hook / IDE (not read by Python code)

| Variable | Purpose |
|----------|---------|
| **`PYRTKAI_PYTHON`** | Absolute path to the **`python`** binary that should run `pyrtkai` from **Cursor** shell hooks (see `integrations/cursor-plugin/`). If unset, wrappers fall back to `pyrtkai` on `PATH` or `python3 -m pyrtkai.cli`. |

## MVP rewrite rules (registry)

Disable a rule with `0`, `false`, `no`, or `off`. Omitted → enabled (defaults below).

| Variable | Default | Effect |
|----------|---------|--------|
| `PYRTKAI_MVP_ENABLE_GIT_STATUS` | enabled | Allow MVP rewrite for `git status`-style commands. |
| `PYRTKAI_MVP_ENABLE_LS` | enabled | `ls` |
| `PYRTKAI_MVP_ENABLE_GREP` | enabled | `grep` |
| `PYRTKAI_MVP_ENABLE_RG` | enabled | `rg` |

## Output filter (proxy)

| Variable | Default | Effect |
|----------|---------|--------|
| `PYRTKAI_OUTPUT_MAX_CHARS` | `4000` | Max characters written per stream after filtering (non-JSON text). |
| `PYRTKAI_TRUNC_MARKER` | `\n...[TRUNCATED]...\n` | Marker between head and tail when truncating. |
| `PYRTKAI_OUTPUT_FILTER_PROFILE` | `truncating` | Filter profile name (MVP: truncating). |

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

## Tests / development only

| Variable | Effect |
|----------|--------|
| `PYRTKAI_ENFORCE_PERF_SLO` | Set to `1` to enforce optional performance bounds in `tests/test_performance_slo.py`. |

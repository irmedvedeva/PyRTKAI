# PyRTKAI

[![PyPI version](https://img.shields.io/pypi/v/pyrtkai.svg)](https://pypi.org/project/pyrtkai/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyrtkai.svg)](https://pypi.org/project/pyrtkai/)
[![CI](https://github.com/irmedvedeva/PyRTKAI/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/irmedvedeva/PyRTKAI/actions/workflows/ci.yml?query=branch%3Amaster)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/irmedvedeva/PyRTKAI/blob/master/LICENSE)
[![Security checks in CI](https://img.shields.io/badge/CI-bandit%20%7C%20pip--audit-informational.svg)](https://github.com/irmedvedeva/PyRTKAI/actions/workflows/ci.yml?query=branch%3Amaster)

> **Less noise. Less risk. Same commands.**  
> **Safe-by-default execution layer** for Cursor and other AI-driven terminals — local, inspectable Python (**stdlib-only** at runtime).

## Summary

| | |
|--|--|
| **What** | CLI **`proxy`**, **`hook`**, **`rewrite`**, output **filtering**, **fail-closed** policy, optional **gain** metrics |
| **Who** | Teams using **Cursor** or any **agent-heavy** shell / automation |
| **Outcome** | **Less wasted context** on huge logs, **fewer shell surprises**, **JSON tool output preserved** when detected |
| **Safety** | **`proxy`** runs the child with **argv-only** subprocess (**no shell**); bad deny-regex config → **deny** |

**Not a ChatGPT/OpenAI client:** no **API keys** or cloud calls for core behavior — see [FAQ](#faq).

## Quickstart (~60 seconds)

Copy-paste into a **clean venv** (Python **3.11+**):

```bash
python3 -m venv .venv && .venv/bin/pip install -U pip pyrtkai
.venv/bin/pyrtkai doctor --json
.venv/bin/pyrtkai proxy python3 -c "print('ok')"
```

**Optional:** stdin/stdout hook JSON:

```bash
printf '%s' '{"tool_input":{"command":"echo hi"}}' | .venv/bin/pyrtkai hook
```

## Features

- **Context optimization** — deterministic truncation + marker; optional **gain** with `tokens_saved_est` / `tokens_saved_pct_est` (char-based **estimates**, not provider tokenizers).
- **Safe execution** — **`proxy`** uses **argv-only** `subprocess` (no shell) for the executed program.
- **Predictable policy** — `PYRTKAI_DENY_REGEXES` / `PYRTKAI_DENY_REGEX`; invalid configuration → **deny** (fail-closed).
- **Stable tool contracts** — JSON / NDJSON **pass-through** when detected.
- **Cursor-ready** — hook adapter, **`doctor`** / **`verify-hook`**, bundle under [`integrations/cursor-plugin/`](integrations/cursor-plugin/README.md).

## Why PyRTKAI exists

- **Noise is expensive** — long command output consumes model context even when the answer is short.
- **Shells are sharp** — agents and wrappers often re-introduce quoting and injection risk.
- **Safety should default closed** — ambiguous policy configuration should **deny**, not silently allow.
- **Thin, inspectable layer** — small codebase, tests, optional local SQLite metrics only.

## Before / after (typical behaviors)

| Situation | Without PyRTKAI | With PyRTKAI |
|-----------|-----------------|--------------|
| Very long `stdout` | Full text reaches the agent/session | Text may be **truncated with a fixed marker** (`PYRTKAI_OUTPUT_MAX_CHARS`) |
| Messy shell pipeline / heredoc | Higher risk and harder reasoning | **`rewrite` tends to skip** risky shapes; **`proxy` stays no-shell** |
| Tool returns JSON | Naive truncation may break parsers | **Structured pass-through** when JSON/NDJSON is detected |
| Bad deny-regex config | Some systems ignore errors | **Fail-closed deny** for invalid policy input |

### Demo: truncated text (real `proxy` output)

```bash
export PYRTKAI_OUTPUT_MAX_CHARS=120
pyrtkai proxy python3 -c "print('x' * 400)"
```

Expect **first half +** default marker **`...[TRUNCATED]...`** **+ last half** (sizes scale with `PYRTKAI_OUTPUT_MAX_CHARS`).

### Demo: JSON unchanged

```bash
pyrtkai proxy python3 -c "import json; print(json.dumps({'ok': True, 'id': 42}))"
```

Valid JSON on one line is **not** shortened by the text filter.

## Compared to common alternatives

| Approach | Trade-off |
|----------|-----------|
| Raw shell for every agent command | **More** shell-injection and quoting risk |
| Ad-hoc `head` / manual copy | Often **breaks structured** output; not a stable contract |
| IDE-only allow/deny lists | Useful, but **host-specific**; PyRTKAI adds a **portable policy + filtering** layer |
| Larger “do everything” CLI proxies | Broader surface; PyRTKAI optimizes for **predictability, tests, and small code** |

## Security

- **No shell in `proxy`:** child processes use **argv-only** `subprocess` — see [SECURITY.md](SECURITY.md) (reporting, scope, threat model).
- **Fail-closed policy:** invalid deny-regex configuration **denies**.
- **Hook integrity:** SHA-256 baseline vs script on disk — `pyrtkai doctor`, `pyrtkai verify-hook --json` ([details](SECURITY.md)).
- **CI:** `ruff`, `mypy`, `bandit`, `pip-audit`, `pip check` ([workflow](https://github.com/irmedvedeva/PyRTKAI/actions/workflows/ci.yml)).

## Cursor integration

Step-by-step guide (install, **`PYRTKAI_PYTHON`**, `hooks.json`, **`verify-hook`**, troubleshooting): **[integrations/cursor-plugin/README.md](integrations/cursor-plugin/README.md)**.

## Installation

The installed command is **`pyrtkai`** (Python **3.11+**).

### From PyPI (typical users)

```bash
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install pyrtkai
.venv/bin/pyrtkai --help
```

Activate the venv or call `.venv/bin/pyrtkai` directly. If **`pyrtkai`** is not on the `PATH` Cursor uses, set **`PYRTKAI_PYTHON`** to your venv’s **`python`** (absolute path).

**PEP 668:** On many Linux distributions, `pip install` into the **system** Python fails with `externally-managed-environment`. Use a **venv** (as above), **pipx**, or another dedicated environment—not `sudo pip` unless you understand the risks.

### From a source clone (contributors, Cursor plugin dev)

Use a venv **in the repository root** and an **editable** install:

```bash
cd /path/to/PyRTKAI
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -e .
.venv/bin/pyrtkai --help
```

**Cursor hook:** set **`PYRTKAI_PYTHON`** to **`.venv/bin/python`** (absolute path) so IDE hooks use the same interpreter.

### Cursor plugin bundle

See **[Cursor integration](#cursor-integration)** and [integrations/cursor-plugin/README.md](integrations/cursor-plugin/README.md).

## Use cases

- **Cursor agent sessions** — shrink noisy `git`/`build`/`test` output before it hits the model; optional **gain** to quantify estimates.
- **Terminal automation** — same filtering/proxy path for scripts that wrap CLI tools.
- **CI / developer machines** — enforce deny patterns (`PYRTKAI_DENY_REGEX*`) at the hook layer alongside IDE rules.
- **Log-heavy commands** — deterministic truncation instead of ad-hoc `head`/`tail` that breaks JSON.

## Benchmarks

Measure **proxy vs direct** subprocess latency ratio (local, no network):

```bash
pyrtkai bench proxy --iters 10 --json -- python3 -c "print(1)"
```

Interpretation: ratios depend on OS and workload; use the same command you care about in production.

## Command reference

Run **`pyrtkai --help`** and **`pyrtkai <subcommand> --help`** for the full CLI.

| Area | Commands |
|------|----------|
| Health / config | `doctor [--json]`, `config [--json]` |
| Core | `rewrite <words…>` (rewrite decision), `proxy <argv…>` (run command with filtering) |
| Cursor hook | `hook` (stdin/stdout JSON), `verify-hook [--json]` |
| Metrics | `gain summary`, `gain export`, `gain history` (optional `--json`, `--limit`); `gain project [--root PATH]` |
| Benchmark | `bench proxy --iters N [--json] -- <argv…>` |

Examples:

- `pyrtkai doctor --json`
- `pyrtkai config --json`
- `pyrtkai rewrite git status`
- `pyrtkai proxy git status`
- `pyrtkai hook` reads hook JSON from stdin and writes the adapted JSON response to stdout.
- `pyrtkai verify-hook --json` verifies the SHA-256 integrity baseline for the installed hook script (when using the Cursor bundle).
- `pyrtkai gain summary --json`
- `pyrtkai gain export --limit 1000`
- `pyrtkai bench proxy --iters 5 --json -- python3 -c "print(1)"`

### Example: `doctor --json` (shape)

Fields vary by machine; expect keys such as `hook_integrity`, `hooks_json`, `mvp_rewrite_rules`, and `output_filter`:

```json
{
  "hook_integrity": {
    "ok": true,
    "reason": "ok",
    "hook_path": "/path/to/pyrtkai-rewrite.sh",
    "baseline_path": "/path/to/pyrtkai-rewrite.sh.sha256"
  },
  "hooks_json": {"present": true, "configured": true},
  "mvp_rewrite_rules": {"git_status": true, "ls": true, "grep": true, "rg": true},
  "output_filter": {"profile": "truncating", "max_chars": 4000}
}
```

### Example: `rewrite` (illustrative)

```bash
pyrtkai rewrite git status
```

Stdout is a **single JSON object** describing rewrite/skip and reasons (exact schema: run the command locally).

## Doctor and config

`pyrtkai doctor` checks local health:

- whether the hook script integrity baseline matches
- whether a `hooks.json` file exists
- whether `hooks.json` is configured to call the expected hook script
- which MVP rewrite rules are currently enabled

The `doctor --json` output includes:

- `hook_integrity.ok`
- `hook_integrity.hook_path` / `hook_integrity.baseline_path` (which files were checked)
- `hooks_json.present`
- `hooks_json.configured`
- `mvp_rewrite_rules`
- `output_filter.profile`
- `output_filter.max_chars`

`pyrtkai config` is a lightweight command for inspecting the enabled MVP rewrite rules:

- `pyrtkai config --json`

## Configuration

**Full reference:** [docs/environment-variables.md](docs/environment-variables.md) (all `PYRTKAI_*` variables in one place).

Environment variables control the rewrite allow list, output truncation, and policy gating.

MVP rewrite enable flags:

- `PYRTKAI_MVP_ENABLE_GIT_STATUS` (default true)
- `PYRTKAI_MVP_ENABLE_LS` (default true)
- `PYRTKAI_MVP_ENABLE_GREP` (default true)
- `PYRTKAI_MVP_ENABLE_RG` (default true)

Any of these values disable the rule:

- `0`
- `false`
- `no`
- `off`

Output filtering:

- `PYRTKAI_OUTPUT_MAX_CHARS` integer >= 0 (default 4000)
- `PYRTKAI_TRUNC_MARKER` marker string (default contains a truncation marker)
- `PYRTKAI_OUTPUT_FILTER_PROFILE` (default `truncating`)

Policy gate deny patterns:

- `PYRTKAI_DENY_REGEXES` comma-separated regex patterns
- `PYRTKAI_DENY_REGEX` single regex
- `PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS` (default `65536`): if the original or rewritten command string exceeds this length while deny patterns are configured, the policy gate **denies** (fail-closed). Mitigates pathological regex cost on huge commands; increase only if needed.

### Limits (doctor and policy)

- **`pyrtkai doctor`** reads `~/.cursor/hooks.json` only if its size is at most **1 MiB**. Larger files are treated as present but not parsed, so `hooks_json.configured` may stay false even when the file exists.
- With **`PYRTKAI_DENY_REGEXES` / `PYRTKAI_DENY_REGEX`** set, very long commands are subject to **`PYRTKAI_DENY_REGEX_MAX_INPUT_CHARS`** (see above).

### Gain tracking (local SQLite)

When **`PYRTKAI_GAIN_ENABLED=1`**, events are stored under **`PYRTKAI_GAIN_DB_PATH`** (default `~/.pyrtkai/gain.sqlite`). Older rows are pruned using **`PYRTKAI_GAIN_RETENTION_DAYS`** (default **30**). Treat the DB path like any local credential store: use a user-writable directory you trust; do not point it at world-writable locations in multi-user setups.

**CLI:** `pyrtkai gain` with **no** subcommand (`summary` / `export` / `history`) behaves the same as **`pyrtkai gain summary`**: both print the aggregated summary (JSON if **`--json`**). Use explicit subcommands when you want export/history or separate `--limit` on summary.

#### Understanding savings (amount and percent)

PyRTKAI does **not** call a model tokenizer. It estimates “tokens” from **character counts** of stdout/stderr (default: **one token ≈ four characters**, overridable with **`PYRTKAI_CHARS_PER_TOKEN`**). That makes numbers **stable and comparable across runs**, but they are **not** identical to provider tokenizer counts.

After commands run through **`pyrtkai proxy`**, read totals with:

```bash
PYRTKAI_GAIN_ENABLED=1 pyrtkai gain summary --json
```

| Field | Meaning |
|--------|---------|
| **`tokens_before`** | Estimated tokens that would correspond to the **full** captured stdout+stderr **before** filtering (pass-through or truncated). |
| **`tokens_after`** | Estimated tokens in what was **actually printed** after filtering (e.g. shorter text if truncation applied). |
| **`tokens_saved_est`** | **`tokens_before` − `tokens_after`**. The “amount” of estimated savings (larger ⇒ more characters removed by the filter). |
| **`tokens_saved_pct_est`** | **100 × `tokens_saved_est` / `tokens_before`**, rounded to two decimals. Share of estimated output “trimmed” **relative to the pre-filter size**. **`null`** when there is nothing to compare (e.g. empty DB or **`tokens_before` is 0**). |

Per-command groupings live under **`by_classification`** (same fields per group, including **`tokens_saved_pct_est`**).

**How to read it:** use **`tokens_saved_est`** for a rough **quantity** of reduction; use **`tokens_saved_pct_est`** to see how **large** that reduction was **relative** to the original output size (e.g. 50% means about half of the estimated pre-filter volume was not printed after filtering). Short runs with little or no truncation often show **0** saved and **0%** (or **`null`** percent when there is no baseline).

### Known limitations (heuristics and deny-regex)

- **Rewrite registry** skips MVP rewrite if the command string contains substrings such as `--json`, `--format`, or `--template` anywhere (conservative; may skip in edge cases such as odd paths).
- **Proxy streaming** treats output that begins (after whitespace) with `{` or `[` as JSON pass-through; rare text that looks like JSON at the start will not be truncated.
- **Deny regexes** (`PYRTKAI_DENY_REGEXES`): input length is capped (see **Limits**), but a regex with catastrophic backtracking can still be expensive on worst-case input within that cap. Prefer simple patterns; for stricter isolation run hooks in a resource-limited environment.

## FAQ

- **Do I need an OpenAI / ChatGPT API key?** **No.** PyRTKAI does not call cloud LLM APIs for its core CLI, `proxy`, or `hook` paths.
- **Why does `pip install` fail on Debian/Ubuntu system Python?** Many distros use **PEP 668** (`externally-managed-environment`). Use a **venv**, **pipx**, or install into a user environment you control — not `sudo pip` unless you understand the risks.
- **`pyrtkai` not on PATH inside Cursor** — set **`PYRTKAI_PYTHON`** to the **absolute** path of the interpreter that has PyRTKAI installed (see [integrations/cursor-plugin/README.md](integrations/cursor-plugin/README.md)).
- **Why was my JSON output not truncated?** Output that looks like **JSON/NDJSON** at the start is treated as **structured pass-through** so tools do not break.
- **How do I loosen or tighten filtering?** See **`PYRTKAI_OUTPUT_MAX_CHARS`**, **`PYRTKAI_OUTPUT_FILTER_PROFILE`**, and [docs/environment-variables.md](docs/environment-variables.md).
- **How do I effectively disable text truncation?** Set **`PYRTKAI_OUTPUT_MAX_CHARS`** to a **very large** value (e.g. `999999999`). There is no separate “off” switch; `0` is not recommended (behavior is edge-case–sensitive).
- **How do I debug a failing hook?** Run **`pyrtkai doctor --json`** and **`pyrtkai verify-hook --json`**; run the hook script from a terminal with the same **`PYRTKAI_PYTHON`** and watch stderr; use **`pyrtkai hook`** with a minimal JSON payload (see [Quickstart](#quickstart-60-seconds)).
- **How do I know the Cursor hook is active?** Run **`pyrtkai doctor --json`** and inspect `hooks_json` / `hook_integrity`; use **`pyrtkai verify-hook --json`** for the bundled script checksum.
- **Where are security vulnerabilities reported?** See [SECURITY.md](SECURITY.md) (private channel — **not** a public issue for undisclosed vulnerabilities).

**License:** [MIT](LICENSE).

## Contributing

- **Contributor guide:** [CONTRIBUTING.md](CONTRIBUTING.md) (tests, linters, packaging, PyPI).
- **Roadmap:** [docs/product-roadmap.md](docs/product-roadmap.md).
- **Forks:** if your canonical GitHub repository is not the one listed in **`[project.urls]`** inside **`pyproject.toml`**, update those URLs so PyPI and metadata point to your repo.
- **Pull requests:** run the same checks as CI before pushing: `make test`, `make lint`, `make typecheck`, and `make security` (or the individual `pytest` / `ruff` / `mypy` / `bandit` / `pip-audit` commands). Optionally run `python -m build` to verify wheels/sdists.
- **Commits:** large documentation-only changes (e.g. under `.doc/`) can be split from code commits if you want a clearer history—optional, not required.

## Development and testing

Common commands:

- `make test`
- `make lint`
- `make typecheck`
- `make security` (same tools as CI when `ruff`, `mypy`, `bandit`, and `pip-audit` are installed)

Direct checks:

- `pytest`
- `ruff check src tests`
- `mypy src tests`
- `bandit -r src -q` (application code; tests use `subprocess` intentionally in harnesses)
- `pip-audit` or `pip-audit --skip-editable` (for a local **editable** install, PyPI may not resolve the package name and `pip-audit` can report *Skip Reason: Dependency not found on PyPI* — that is expected; CI uses a normal install from the repo)

### Optional: bandit on tests

To scan `tests/` with relaxed skips (assert/subprocess/random in harnesses), use the bundled config:

- `bandit -c bandit-tests.yaml -r tests -q`

### Performance SLO (optional)

Loose proxy-overhead checks live in **`tests/test_performance_slo.py`**. Local run:

```bash
PYRTKAI_ENFORCE_PERF_SLO=1 pytest -q tests/test_performance_slo.py
```

### Profiling slow deny-regex / hook paths (optional)

PyRTKAI does not ship a regex timeout. If policy matching feels slow, simplify `PYRTKAI_DENY_REGEXES`, reduce pattern complexity, or profile locally, e.g. `python -m cProfile -m pyrtkai.cli rewrite 'your command string'` and inspect hotspots.

### Example: token economy (gain)

With an editable venv install, enable gain and point the DB to a temp file, run a proxy command that prints more characters than **`PYRTKAI_OUTPUT_MAX_CHARS`** (default 4000), then inspect estimated token savings:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
export PYRTKAI_GAIN_ENABLED=1
export PYRTKAI_GAIN_DB_PATH=/tmp/pyrtkai_gain_demo.sqlite
rm -f /tmp/pyrtkai_gain_demo.sqlite

.venv/bin/pyrtkai proxy python3 -c "print('x'*12000)" >/dev/null
.venv/bin/pyrtkai gain summary --json
```

On a typical run (default `PYRTKAI_CHARS_PER_TOKEN=4`, default max chars 4000), JSON output is similar to: `tokens_before` ≈ 3000, `tokens_after` ≈ 1000, `tokens_saved_est` ≈ 2000 — **exact numbers depend on your environment and truncation**. Use `pyrtkai bench proxy --iters 5 <command...>` to measure proxy overhead (latency ratio vs direct `subprocess`); ratios vary by machine.

### Gain DB inside this repo (local only)

To keep metrics under the project tree (ignored by git via `.pyrtkai/` in `.gitignore`):

```bash
export PYRTKAI_GAIN_ENABLED=1
export PYRTKAI_GAIN_DB_PATH="$PWD/.pyrtkai/gain.sqlite"
pyrtkai proxy <command...>   # or: PYTHONPATH=src python3 -m pyrtkai.cli proxy ...
pyrtkai gain summary --json
pyrtkai gain export --limit 500
```

Replace `pyrtkai` with `.venv/bin/pyrtkai` if you use a venv. Only commands run through **`proxy`** while gain is enabled are recorded.

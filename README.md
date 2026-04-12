# PyRTKAI

PyRTKAI reduces **CLI noise** in AI agent workflows: a **Python**-based command proxy, conservative rewrite decisions, and output filtering to cut wasted context. The focus is **inspectable code**, explicit safety defaults (**no shell** in the proxy path, **fail-closed** policy), and **testability**.

## Goals

- **Python-only** deployment and straightforward security review of the codebase.
- First-class **Cursor** integration via `integrations/cursor-plugin/` with `doctor` / `verify-hook`.
- **Predictable** behavior over chasing maximum command coverage in a single release.

## Key ideas

1. Local execution only. The proxy runs commands without a shell to avoid accidental interpretation of shell metacharacters.
2. Conservative rewrite. If the input command looks risky (unbalanced quotes, heredocs, shell operators outside quotes), PyRTKAI returns a skip decision.
3. Fail closed policy gate. Policy parsing and matching are designed so that misconfiguration defaults to denial.
4. Structured output preservation. JSON and NDJSON outputs pass through unchanged to keep downstream parsing valid.
5. Token waste reduction. Text outputs can be truncated deterministically with a configurable marker.

## Installation

The installed command is **`pyrtkai`** (Python **3.11+**).

### From PyPI (typical users)

```bash
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install pyrtkai
.venv/bin/pyrtkai --help
```

If **`pip install pyrtkai`** fails (name not on PyPI yet), use **From a source clone** below until the first release is published.

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

A Cursor Marketplace–style layout (manifest, `hooks/hooks.json`, shell wrapper) lives under **`integrations/cursor-plugin/`**. See that directory’s **README** for **`PYRTKAI_PYTHON`**, merging into `~/.cursor/hooks.json`, and either **`pip install pyrtkai`** or an editable install from this repo.

## Usage

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

## Security posture

PyRTKAI is designed to avoid unsafe shell behavior by default:

- `pyrtkai proxy` executes commands without invoking a shell
- rewrite decisions are conservative and skip risky patterns
- JSON and NDJSON outputs are preserved to avoid breaking structured tool responses
- policy parsing is fail closed (invalid deny configuration denies)

The project uses defense-in-depth checks in CI, including:

- `ruff`
- `mypy`
- `bandit`
- `pip-audit`

**License:** [MIT](LICENSE). **Reporting security issues:** see [SECURITY.md](SECURITY.md).

## Contributing

- **Roadmap:** product direction and ecosystem watch list — [docs/product-roadmap.md](docs/product-roadmap.md).
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

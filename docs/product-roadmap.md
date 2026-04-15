# PyRTKAI — product development roadmap

This document tracks **planned product steps** and a **watch list** of adjacent tools and patterns (token cost, memory, search, MCP). It is updated from time to time; dates refer to ecosystem research, not release commitments.

## Strategic focus (unchanged)

- **CLI path**: safe proxy, conservative rewrite, deterministic output filtering, local **gain** metrics.
- **Differentiation**: inspectable Python, fail-closed policy, Cursor-oriented bundle — not “another generic memory product.”

---

## Near-term product steps (PyRTKAI codebase)

1. **PyPI & install UX** — First-class `pip install pyrtkai`, smoke tests from a clean venv, version/tags aligned with `pyrtkai.__version__`. *(Done: clean-venv install smoke in CI + local `make smoke-install`; publish workflow fails on release tag/version mismatch.)*
2. **Gain & benchmarks** — Document “when savings are non-zero” (output larger than limits); optional CI smoke for `gain summary` + `bench proxy` on a fixed command. *(Done: [environment-variables.md](environment-variables.md) gain subsection; CI smoke in `.github/workflows/ci.yml`.)*
3. **Rewrite coverage** — Expand MVP rewrite registry cautiously (tests-first), keep skip heuristics for risky shell shapes.
   - **Safety gate per new rule:** command must stay argv-safe (no shell evaluation, no implicit interpolation). ✅
   - **Policy parity:** deny-regex check must continue to evaluate both original and rewritten command. ✅
   - **Skip-first on ambiguity:** if parsing sees heredoc/metachar/unbalanced structure risk, keep `skip` + explain/suggestion (no forced rewrite). ✅
   - **Regression tests per rule:** positive rewrite path + deny path + malformed/risky shape path. ✅
   - **Rollout switch:** each rule behind `PYRTKAI_MVP_ENABLE_*` toggle so maintainers can disable quickly. ✅
   - **Implemented:** stable rewrite metadata (`rewrite_rule_id`, `suggested_disable_env`), rule-level explain/remediation, conservative `git log` rule (`PYRTKAI_MVP_ENABLE_GIT_LOG`), and hook-side rewrite hint where payload schema allows (no auto-allow path changes).
4. **Cursor plugin** — Keep `integrations/cursor-plugin/` in sync with released package; marketplace checklist when repo is public. *(Progress: plugin README + pre-publish checklist synced with `init --quickstart`, `status --json`, rewrite opt-out toggles, and JSON `_meta` notes.)*
5. **Observability** — Clear JSON fields in `doctor` / `gain` for dashboards; avoid breaking schema without a version bump. *(Progress: additive `_meta` with stable `schema`/`schema_version` in `doctor`, `status`, and gain summary JSON paths.)*
6. **Security** — Keep subprocess argv-only execution, policy tests, `bandit` / `pip-audit` in CI; review hook script surface. *(Progress: `pyrtkai hook` now caps stdin bytes via `PYRTKAI_HOOK_MAX_STDIN_BYTES` with fail-closed deny on overflow; wrapper uses `exec --` for `PYRTKAI_PYTHON` path hardening.)*

---

## Medium-term (architecture)

1. **CLI dispatch** — If subcommands keep growing, replace long `if` chains with a small dispatch table (same public CLI). *(Done in `cli.py`; public CLI unchanged.)*
2. **Optional MCP** — Evaluate an MCP surface *only if* it fits “thin tools + local execution”: e.g. expose `proxy`/`gain summary`/`doctor` as MCP tools with **minimal** schema tokens (see “Code mode” below). Not a goal to replicate another CLI proxy’s full command surface. *(Progress: thin-surface contract doc in [mcp-thin-surface.md](mcp-thin-surface.md) + contract tests in `tests/test_json_contracts.py` and `tests/test_proxy_contracts.py`; schema/version policy centralized in `src/pyrtkai/schema_meta.py`.)*
3. **Documentation** — Single “operations” page: env vars, limits, troubleshooting for agent users. *(See [operations.md](operations.md).)*

---

## Ecosystem watch list (research — 2025–2026)

Adjacent work in the ecosystem (tokens, memory, agents) is useful for **ideas and benchmarking**, not as default dependencies.

### CLI / terminal token reduction

- Other stacks ship **high-performance CLI proxies** with broad command coverage; PyRTKAI stays **Python-first** and safety-biased.
- **Agent shell noise** is the same problem space as our `proxy` + filters — compare **gain** on comparable workloads (heuristic vs tokenizer).

### MCP: tool schema cost & “code mode”

Large MCP servers burn context on **tool definitions**. Common pattern: **few tools + code execution** so the model loads APIs on demand instead of thousands of tool schemas.

- [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) (Anthropic engineering) — reduces upfront **tools/list** tokens.
- Broader “code mode” + OpenAPI patterns — e.g. two tools (`search` + `execute`) vs one tool per REST endpoint.

**Takeaway for PyRTKAI:** if we ever add MCP, prefer **narrow tool surfaces** and structured JSON responses; avoid duplicating a huge tool matrix in the prompt.

### MCP: memory, search, and tooling (generic)

- **Slimmer MCP memory bridges** — compress tool definitions vs default memory servers; orthogonal to our core CLI path.
- **Token-oriented MCP servers** — caching, chunking, caps; useful reference for **payload** limits.
- **Graph or long-term memory MCPs** — retrieval across sessions vs **per-command** CLI compression (complementary, not a substitute).
- **MCP CLI clients** — JSON/scripting interfaces for **inspecting** what agents load.

### Web / internet search for agents

Agents need **current** facts; piping raw HTML is an anti-pattern. That problem sits on a **different axis** from PyRTKAI (we optimize **local shell** output). Typical patterns: LLM-oriented search APIs, MCP search tools, `fetch` + extraction with body caps, multi-provider routers — each has token and trust-boundary trade-offs.

**PyRTKAI scope:** we do **not** aim to replicate web search. **PyRTKAI** shrinks terminal noise; **MCP search** or the IDE’s web tool handles the internet. Future work here is mostly **documentation** (configure both without double-counting noise) unless users ask for a thin workflow.

### Standards & agents SDK

- **OpenAI Agents SDK / hosted MCP** — `deferLoading` / tool search patterns ([docs](https://openai.github.io/openai-agents-js/guides/mcp)).
- **MCP spec evolution** — Prefer official SDKs and small composable servers over ad-hoc giant tool lists.

---

## What we explicitly defer

- **Replacing** dedicated long-term memory products (graph memory, narrative “memory palace” patterns, etc.).
- **One-tool-per-endpoint** MCP generators without a token budget story.
- **Cloud telemetry** by default — PyRTKAI stays local-first unless opt-in is designed and documented.

---

## Action backlog (feedback: strengths vs gaps)

Honest positioning: PyRTKAI is **stronger on safety and predictability** (no shell in `proxy`, fail-closed policy, conservative rewrite, JSON pass-through, local **gain**). The main gap is **onboarding UX**, **immediate visible value**, and **optional “helpful” guidance** when skipping — without trading away safety.

### P0 — Onboarding (highest leverage)

- [x] **`pyrtkai init`** — one command after `pip install`: print version, interpreter, `PYRTKAI_PYTHON` hint, next commands; `--json` / `--with-doctor` for automation (merge hints for `hooks.json` remain documented in the Cursor bundle README).
- [x] **Time-to-first-success target** — **`pyrtkai init --quickstart`** + README; **`init --json`** includes **`easy_start`** for automation.
- [x] **Cursor-first copy** — README tagline + guided path above the fold (safe-by-default shell layer for Cursor / agent terminals).

### P1 — Prove value immediately

- [x] **Post-run summary (optional)** — `pyrtkai proxy --summary` or `PYRTKAI_PROXY_SUMMARY=1`: one stderr line with char + **estimated token** savings (heuristic; aligns with gain’s char-based token estimate).
- [x] **`pyrtkai status`** — one-screen / `--json` snapshot: version, embedded **`doctor`** payload, optional **gain** aggregate (when `PYRTKAI_GAIN_ENABLED=1`).
- [x] **Built-in demo / smoke** — README quickstart + truncation demo (`PYRTKAI_OUTPUT_MAX_CHARS=120`) + `proxy --summary`.

### P2 — “Soft magic” (still safe-by-default)

- [x] **Suggested safer alternative** — `rewrite` JSON may include **`suggested_command`** (argv-safe / `shlex.join`); hooks may include **`explain`** on deny / malformed input (see `rewrite_hints.py`).
- [x] **`--explain` (or JSON field)** — `pyrtkai rewrite --explain` adds an **`explain`** block; policy / hook denies include **`explain`** with stable **`code`** where the schema allows.
- [x] **Guardrails** — conservative suggestions only; regression tests for rewrite / policy / hook JSON (no new shell execution paths in suggestions).

### P2b — Positioning & demos *without* weakening the threat model

Users often compare on **convenience and instant “wow”**; our stack optimizes **argv-only execution, fail-closed policy, and predictable output handling**. Tasks below are **documentation, messaging, and measurable demos** — not hosted command generation or a full terminal product.

- [x] **Positioning one-pager** — [docs/workflows-and-positioning.md](workflows-and-positioning.md) (matrix + links to `SECURITY.md`).
- [x] **“Blocked + why” consistency** — hook provider table + **`explain.code`** note in that doc; pass-through **`{}`** called out.
- [x] **Same-command benchmark story** — copy-paste block (baseline vs `proxy --summary`) in [docs/workflows-and-positioning.md](workflows-and-positioning.md).
- [x] **Time-to-value copy** — **`init --quickstart`** + README; JSON **`easy_start`** for tooling.

**Explicitly out of scope (security / product policy):**

- Default **LLM-generated shell** or **unsupervised auto-execution** of user commands inside PyRTKAI.
- **shell=True** or loosening argv-only **`proxy`** semantics for convenience.
- **Bundled rich terminal UI** or first-class shell autocomplete as a product (optional third-party integration docs only).

### P3 — Ecosystem & trust signals (over time)

- [x] **GitHub topics / release cadence** — topic examples + release checklist in [CONTRIBUTING.md](../CONTRIBUTING.md); [CHANGELOG.md](../CHANGELOG.md) for version notes.
- [x] **Examples repo or docs recipes** — [docs/recipes.md](recipes.md) (five workflows).
- [x] **Community** — GitHub issue forms (bug / feature) under `.github/ISSUE_TEMPLATE/`; security via private advisory link in `config.yml`; no cloud telemetry by default (see “What we explicitly defer”). Optional **GitHub Discussions** remains a maintainer/repo setting, not enforced here.

### Success metrics (30-day direction, not a guarantee)

| Metric | Intent |
|--------|--------|
| Init → `doctor` “ok” rate | Majority of new installs complete happy path |
| Repeat `proxy` usage | Users run wrapped commands regularly, not one-off |
| Stated savings visible | Users report seeing **% / counts** without digging into `gain` SQL |

---

## Related docs

- [Environment variables](environment-variables.md) — full `PYRTKAI_*` list for users and integrators.
- [Workflows & positioning](workflows-and-positioning.md) — short matrix, hook provider summary, benchmark snippet.
- [Recipes](recipes.md) — copy-paste Cursor / agent workflows.
- [Operations index](operations.md) — env, recipes, security, troubleshooting table.
- [MCP thin surface](mcp-thin-surface.md) — small JSON contract and compatibility rules for evaluation.

## How to use this file

- **Contributors:** propose roadmap items via issues/PRs; keep scope aligned with `README.md` and `SECURITY.md`.
- **Maintainers:** trim or archive bullets when superseded; link release posts from GitHub Releases when shipped.

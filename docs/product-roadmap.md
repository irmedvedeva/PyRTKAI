# PyRTKAI — product development roadmap

This document tracks **planned product steps** and a **watch list** of adjacent tools and patterns (token cost, memory, search, MCP). It is updated from time to time; dates refer to ecosystem research, not release commitments.

## Strategic focus (unchanged)

- **CLI path**: safe proxy, conservative rewrite, deterministic output filtering, local **gain** metrics.
- **Differentiation**: inspectable Python, fail-closed policy, Cursor-oriented bundle — not “another generic memory product.”

---

## Near-term product steps (PyRTKAI codebase)

1. **PyPI & install UX** — First-class `pip install pyrtkai`, smoke tests from a clean venv, version/tags aligned with `pyrtkai.__version__`.
2. **Gain & benchmarks** — Document “when savings are non-zero” (output larger than limits); optional CI smoke for `gain summary` + `bench proxy` on a fixed command.
3. **Rewrite coverage** — Expand MVP rewrite registry cautiously (tests-first), keep skip heuristics for risky shell shapes.
4. **Cursor plugin** — Keep `integrations/cursor-plugin/` in sync with released package; marketplace checklist when repo is public.
5. **Observability** — Clear JSON fields in `doctor` / `gain` for dashboards; avoid breaking schema without a version bump.
6. **Security** — Keep subprocess argv-only execution, policy tests, `bandit` / `pip-audit` in CI; review hook script surface.

---

## Medium-term (architecture)

1. **CLI dispatch** — If subcommands keep growing, replace long `if` chains with a small dispatch table (same public CLI).
2. **Optional MCP** — Evaluate an MCP surface *only if* it fits “thin tools + local execution”: e.g. expose `proxy`/`gain summary`/`doctor` as MCP tools with **minimal** schema tokens (see “Code mode” below). Not a goal to replicate another CLI proxy’s full command surface.
3. **Documentation** — Single “operations” page: env vars, limits, troubleshooting for agent users.

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

## Related docs

- [Environment variables](environment-variables.md) — full `PYRTKAI_*` list for users and integrators.

## How to use this file

- **Contributors:** propose roadmap items via issues/PRs; keep scope aligned with `README.md` and `SECURITY.md`.
- **Maintainers:** trim or archive bullets when superseded; link release posts from GitHub Releases when shipped.

# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
for the **Python package** version in `pyrtkai.__version__`.

## [Unreleased]

## [0.1.3] - 2026-04-15

### Added

- User-facing docs: [docs/recipes.md](docs/recipes.md), [docs/workflows-and-positioning.md](docs/workflows-and-positioning.md), [docs/operations.md](docs/operations.md); gain “when non-zero” notes in [docs/environment-variables.md](docs/environment-variables.md).
- GitHub issue forms: bug report and feature request under `.github/ISSUE_TEMPLATE/`.
- CI smoke step: `bench proxy` + `gain summary` with a fixed truncated `proxy` run (`.github/workflows/ci.yml`).
- CI smoke step: clean-venv install (`pip install .`) + `pyrtkai init --json` / `status --json` checks.
- Rewrite rule metadata in CLI JSON: `rewrite_rule_id` and `suggested_disable_env` on rewrite paths, including rule-level remediation with `rewrite --explain`.
- Conservative MVP rewrite rule for `git log` behind `PYRTKAI_MVP_ENABLE_GIT_LOG` (skip on `--json` / `--template` / `--format`).
- Hook diagnostics add a soft `rewriteRuleHint` where payload schema allows (without changing allow/deny semantics).
- Observability metadata: additive `_meta` (`schema`, `schema_version`) in `doctor`, `status`, and gain JSON summary outputs.
- Cursor plugin docs sync: bundle README / pre-publish checklist updated for `init --quickstart`, `status --json`, rewrite rule opt-out toggles, and JSON `_meta` notes.
- Publish guard for release hygiene: workflow check enforces `release tag vX.Y.Z` matches `pyrtkai.__version__`.
- Hook surface hardening: `pyrtkai hook` enforces `PYRTKAI_HOOK_MAX_STDIN_BYTES` (fail-closed on oversized stdin) and Cursor wrapper uses `exec --` for `PYRTKAI_PYTHON` execution path.
- Install UX hardening: added `make smoke-install` and CI clean-venv check now verifies `status --json` version matches installed `pyrtkai.__version__`.
- Optional MCP prep: added thin JSON surface contract doc (`docs/mcp-thin-surface.md`) and contract tests (`tests/test_json_contracts.py`) for stable top-level fields.
- Schema versioning tech-debt start: centralized `_meta` schema policy in `src/pyrtkai/schema_meta.py` and refactored `doctor` / `status` / `gain` JSON emitters to use it.
- Optional MCP depth: documented `proxy` tool contract + safety limits in `docs/mcp-thin-surface.md` and added `tests/test_proxy_contracts.py`.

### Fixed

- `init --quickstart --with-doctor` now remains non-blocking for onboarding: doctor output is printed, but quickstart exits `0` even when local hook setup is incomplete.
- Type-checking fix in `tests/test_schema_meta.py` for `dict[str, object]` invariance and `_meta` indexing under `mypy`.
- `rewrite --explain` skip text now lists the current MVP rewrite set including `git log`.

## [0.1.2]

- Published package version; release artifacts and notes: [GitHub Releases](https://github.com/irmedvedeva/PyRTKAI/releases).

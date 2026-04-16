# MCP thin surface (evaluation notes)

This document captures a **minimal JSON contract** that can be exposed by an MCP adapter
without mirroring the full CLI command matrix.

Goal: keep MCP token cost and tool schema size small, while preserving PyRTKAI's
security model (argv-only execution, fail-closed policy, deterministic outputs).

## Candidate MCP tools (small surface)

- `status` -> calls `pyrtkai status --json`
- `doctor` -> calls `pyrtkai doctor --json`
- `gain_summary` -> calls `pyrtkai gain summary --json`
- `rewrite` -> calls `pyrtkai rewrite --explain <command...>`
- `proxy` -> calls `pyrtkai proxy [--summary] -- <argv...>` with strict adapter-side guardrails

These four cover most operational workflows without exposing broad shell execution.
`proxy` is optional and should be exposed only with conservative adapter policies.

## Stable top-level contract (v1)

All JSON payloads should preserve existing keys and may add fields over time.
Current additive schema marker:

- `_meta.schema`
- `_meta.schema_version` (currently `1`)

Expected `_meta.schema` values:

- `status` payload: `status`
- `doctor` payload: `doctor`
- `gain summary` payload: `gain_summary`
- `gain project` payload: `gain_project_summary`

`rewrite` payload currently does not include `_meta`, but has stable keys used by
automation:

- always: `action`, `reason`
- on skip: `skip_code`, optional `suggested_command`
- on rewrite: `rewritten_cmd`, `rewrite_rule_id`, `suggested_disable_env`
- with `--explain`: `explain` (`code`, `why`, `remediation`)

`proxy` is stream-oriented (stdout/stderr passthrough, non-JSON), but adapters can rely on:

- exit code parity with child process (`proxy` returns child return code)
- JSON/NDJSON stdout pass-through when detected (no truncation marker injection)
- optional summary signal on stderr with `--summary`:
  - line starts with `[pyrtkai]`
  - includes `output chars`, `saved`, and token estimate wording
  - marked as heuristic (`(heuristic; not a model tokenizer)`)

## Proxy safety limits for MCP adapters

If exposing a `proxy` MCP tool, keep the adapter conservative:

- pass command as argv array; never construct shell strings
- cap command length and argument count at adapter level
- do not expose shell compound syntax as first-class fields
- prefer allow-listing command families for hosted/shared environments
- preserve PyRTKAI fail-closed behavior for policy checks (do not auto-allow on adapter side)

## Compatibility policy

- Additive fields are allowed without a version bump.
- Renames/removals of existing top-level keys require a schema/version migration note.
- Contract tests in `tests/test_json_contracts.py` guard these invariants.
- Schema IDs and versioning policy are centralized in `src/pyrtkai/schema_meta.py`
  (single source of truth for `_meta.schema` / `_meta.schema_version`).

## Out of scope for MCP evaluation

- Exposing arbitrary shell execution as an MCP tool.
- Reproducing one-tool-per-endpoint surfaces.
- Any path that weakens `proxy` argv-only behavior or fail-closed policy.

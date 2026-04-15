# Operations (index)

Single entry point for running and integrating PyRTKAI day to day.

| Topic | Doc |
|-------|-----|
| Environment variables | [environment-variables.md](environment-variables.md) |
| Copy-paste workflows | [recipes.md](recipes.md) |
| Positioning, hook shapes, benchmark snippet | [workflows-and-positioning.md](workflows-and-positioning.md) |
| MCP thin JSON surface (evaluation) | [mcp-thin-surface.md](mcp-thin-surface.md) |
| Threat model & reporting | [SECURITY.md](../SECURITY.md) |
| Release & CI parity | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| Roadmap | [product-roadmap.md](product-roadmap.md) |

## Quick commands

```bash
pyrtkai init --quickstart
pyrtkai status --json
pyrtkai doctor --json
```

## Troubleshooting

| Symptom | Check |
|---------|--------|
| `pyrtkai` not found in IDE hook | Set **`PYRTKAI_PYTHON`** to the venv **`python`** (absolute path); see Cursor bundle README. |
| Hook returns `{}` | Expected for some hosts when policy denies or there is nothing to rewrite — see [workflows-and-positioning.md](workflows-and-positioning.md). |
| `gain summary` always empty | Set **`PYRTKAI_GAIN_ENABLED=1`** and run **`pyrtkai proxy`** at least once. |
| No savings in gain | Output may be JSON pass-through or under **`PYRTKAI_OUTPUT_MAX_CHARS`** — see [environment-variables.md](environment-variables.md) (gain section). |

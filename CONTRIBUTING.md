# Contributing

See the **Contributing** section in [README.md](README.md) for fork metadata (`pyproject.toml` URLs), PR expectations, and optional doc/code commit splits.

## Pre-merge checklist (match CI)

```bash
make test
make lint
make typecheck
make security   # or install bandit / pip-audit as in Makefile
```

Optional: `python -m build` to verify wheel/sdist.

## Forks

If your canonical GitHub repository differs from the URLs in `[project.urls]` in `pyproject.toml`, update them before publishing packages or pointing users at metadata.

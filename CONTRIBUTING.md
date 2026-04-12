# Contributing

See the **Contributing** section in [README.md](README.md) for fork metadata (`pyproject.toml` URLs), PR expectations, and optional doc/code commit splits.

## Pre-merge checklist (match CI)

Run the same tools the workflow uses:

| Step | Command |
|------|---------|
| Tests | `make test` → `pytest` |
| Lint | `make lint` → `ruff check src tests` |
| Types | `make typecheck` → `mypy src tests` |
| Security | `make security` → `pip check`, `ruff`, `mypy`, `bandit -r src`, `pip-audit` (when installed) |

Optional: `python -m build` to verify wheel/sdist before a release.

## Maintainer: open repo + PyPI (manual)

These steps need accounts and human verification; they are not automated here.

**Repository (public)**

- Set GitHub description, topics, and ensure [SECURITY.md](SECURITY.md) is linked from the repo.
- Confirm no secrets in tracked files or history (`.env`, API keys, private paths).
- `.gitignore` should include local-only trees such as `.doc/`, `.cursor/`, `.pyrtkai/`.
- Tag releases (e.g. `v0.1.0`) and add short release notes.

**PyPI**

- Confirm the project name on [pypi.org](https://pypi.org/) (e.g. `pyrtkai`).
- Use a PyPI account with 2FA; create an API token or configure [Trusted Publishing](https://docs.pypi.org/trusted-publishers/).
- Install build tools once: `pip install build twine` (or use your existing tool versions).
- From a **clean** git checkout at the release commit:

  ```bash
  rm -rf dist/ build/ src/*.egg-info
  python -m build
  twine check dist/*
  ```

- Test upload (optional): `twine upload --repository testpypi dist/*`
- Production: `twine upload dist/*` (uses `~/.pypirc` or `TWINE_USERNAME` / `TWINE_PASSWORD` for token auth).
- Align `src/pyrtkai/__version__.py` with the Git tag (e.g. `v0.1.0` ↔ `0.1.0`).
- Smoke-test: `pip install pyrtkai` in a fresh venv; run `pyrtkai --help` and `pyrtkai doctor --json`.

## Forks

If your canonical GitHub repository differs from the URLs in `[project.urls]` in `pyproject.toml`, update them before publishing packages or pointing users at metadata.

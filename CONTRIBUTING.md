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
- Build and upload: `python -m build`, then `twine check dist/*`, test on [TestPyPI](https://test.pypi.org/) if desired, then `twine upload dist/*`.
- Align `pyrtkai.__version__` with the release tag.
- Smoke-test: `pip install pyrtkai` in a fresh venv.

## Forks

If your canonical GitHub repository differs from the URLs in `[project.urls]` in `pyproject.toml`, update them before publishing packages or pointing users at metadata.

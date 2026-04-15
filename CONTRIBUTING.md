# Contributing

Start with the project overview, quickstart, and FAQ in [README.md](README.md). This file lists **CI parity commands**, **PyPI release** steps, and **fork metadata** expectations (`pyproject.toml` URLs).

## Pre-merge checklist (match CI)

Run the same tools the workflow uses:

| Step | Command |
|------|---------|
| Tests | `make test` → `pytest` |
| Install smoke | `make smoke-install` (fresh venv, `pip install .`, `init/status/doctor` checks) |
| Lint | `make lint` → `ruff check src tests` |
| Types | `make typecheck` → `mypy src tests` |
| Security | `make security` → `pip check`, `ruff`, `mypy`, `bandit -r src`, `pip-audit` (when installed) |

Optional: `python -m build` to verify wheel/sdist before a release.

## Maintainer: open repo + PyPI (manual)

These steps need accounts and human verification; they are not automated here.

**Repository (public)**

- Set GitHub description and **topics** (examples: `python`, `cli`, `cursor`, `ai-agents`, `developer-tools`, `terminal`, `subprocess`, `hooks`, `context-optimization`). Ensure [SECURITY.md](SECURITY.md) is linked from the repo.
- Enable **Dependabot** security updates (and review PRs from [.github/dependabot.yml](.github/dependabot.yml) for Actions + pip).
- Confirm no secrets in tracked files or history (`.env`, API keys, private paths).
- `.gitignore` should include local-only trees such as `.doc/`, `.cursor/`, `.pyrtkai/`.
- Tag releases (e.g. `v0.1.0`) and add short release notes.

**PyPI**

- Confirm the project name on [pypi.org](https://pypi.org/) (e.g. `pyrtkai`).
- Use a PyPI account with 2FA; prefer [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) with the repository workflow `.github/workflows/publish.yml` (environment `pypi`).
- Install build tools once: `pip install build twine` (or use your existing tool versions).
- From a **clean** git checkout at the release commit:

  ```bash
  rm -rf dist/ build/ src/*.egg-info
  python -m build
  twine check dist/*
  ```

- Test upload (optional): `twine upload --repository testpypi dist/*`
- Production: either publish a GitHub Release (triggers Trusted Publishing) or run `twine upload dist/*` manually (uses `~/.pypirc` or `TWINE_USERNAME` / `TWINE_PASSWORD`).
- Align `pyrtkai.__version__` in `src/pyrtkai/__init__.py` with the Git tag (e.g. `v0.1.0` ↔ `0.1.0`).
- Smoke-test: `pip install pyrtkai` in a fresh venv; run `pyrtkai --help` and `pyrtkai doctor --json`.

## Release checklist (each version)

- Update [CHANGELOG.md](CHANGELOG.md) (move `[Unreleased]` items under the new version heading, then add a fresh `[Unreleased]`).
- Bump `pyrtkai.__version__` in `src/pyrtkai/__init__.py` and align the Cursor plugin manifest if needed.
- Run `make test` (or `pytest`) and `make lint` / `make typecheck` / `make security` locally.
- Run `make smoke-install` before release to verify clean install UX from package artifacts.
- `python -m build` and `twine check dist/*` (or rely on the **Publish to PyPI** workflow after a GitHub Release).
- Tag `vX.Y.Z`, publish **GitHub Release** (triggers `.github/workflows/publish.yml` when configured).
- Publish workflow enforces `tag vX.Y.Z == src/pyrtkai/__init__.py::__version__` for release events; mismatch fails before upload.
- Smoke-test: fresh venv `pip install pyrtkai==X.Y.Z` and `pyrtkai doctor --json`.

## Forks

If your canonical GitHub repository differs from the URLs in `[project.urls]` in `pyproject.toml`, update them before publishing packages or pointing users at metadata.

# Security

## Supported versions

Security fixes are applied to the **default branch** of this repository (`master` or `main`, as configured). Use the latest commit or tagged release when deploying.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for undisclosed security vulnerabilities.

1. If the repository is hosted on GitHub and **GitHub Security Advisories** are enabled: use **“Report a vulnerability”** on the repository’s **Security** tab.
2. Otherwise, contact the maintainers through a **private** channel they publish (e.g. security email in repository settings or org policy).

Include:

- A short description of the issue and affected component (e.g. `pyrtkai hook`, `proxy`, `policy`).
- Steps to reproduce or a proof-of-concept **without** exfiltrating user data.
- Your assessment of impact (confidentiality / integrity / availability) if known.

We aim to acknowledge reports within a few business days; timelines depend on severity and maintainer availability.

## What is (and is not) a security issue

**Report privately** (not as a public issue) when a flaw could let an attacker or untrusted input **bypass intended safety** (e.g. unexpected shell invocation from `proxy`, policy gate failing open on invalid config, hook JSON handling that enables injection).

**Use a normal issue** for bugs that do not cross a trust boundary (e.g. rewrite skips on edge-case quoting, truncation heuristics, documentation, UX).

## Threat model (short)

- **Shell injection in `proxy`:** the proxy path is designed to execute **argv-only** (no shell) for the child process; report if you find a path where shell metacharacters are interpreted contrary to that design.
- **Policy gate:** deny-regex configuration is **fail-closed**; report if invalid or missing config is treated as allow.
- **Structured output:** JSON/NDJSON is preserved when detected; report if you can show systematic breakage of structured tool output without an explicit opt-out.
- **Host vs hook:** IDE/agent permission UIs are **outside** PyRTKAI; we still aim for hook responses that do not **override** a local deny with a blanket allow.

## Cursor hook integrity

The Cursor bundle ships a hook script and a **SHA-256 baseline** file. **`pyrtkai doctor`** and **`pyrtkai verify-hook --json`** compare the on-disk script to that baseline. If the script is **replaced or tampered with**, integrity checks fail — treat that like any other local compromise of developer tooling (reinstall from a trusted source, verify git checkout).

## Scope notes

- **`PYRTKAI_PYTHON`** and hook `PATH` are **user-controlled** by design: only point them at interpreters you trust.
- PyRTKAI runs **local** subprocesses; treat hook and proxy configuration like any privileged developer tooling.
- **Host permission models** (IDE allow/deny lists, agent policies) are **not** read by PyRTKAI. Use **`PYRTKAI_DENY_REGEXES` / `PYRTKAI_DENY_REGEX`** to enforce blocks at the hook layer in addition to any IDE rules. The hook avoids emitting a blanket **allow** when local policy denies, and uses **pass-through `{}`** where the host should decide (e.g. Cursor, Gemini when denied).

## Dependency policy

The **runtime package** intentionally keeps **no mandatory third-party dependencies** (stdlib-first). **Development** tools (`pytest`, `ruff`, `mypy`, `bandit`, `pip-audit`) are optional extras; upgrade them when CI or security scans flag issues, and prefer minimal version bumps compatible with supported Python versions.

Maintainers should enable **GitHub Dependabot / security alerts** for this repository and review update PRs (see `.github/dependabot.yml` for scheduled **Actions** and **pip** ecosystem bumps).

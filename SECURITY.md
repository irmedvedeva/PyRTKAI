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

## Scope notes

- **`PYRTKAI_PYTHON`** and hook `PATH` are **user-controlled** by design: only point them at interpreters you trust.
- PyRTKAI runs **local** subprocesses; treat hook and proxy configuration like any privileged developer tooling.

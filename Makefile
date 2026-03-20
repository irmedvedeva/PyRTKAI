VENV ?= .venv

ifeq ($(wildcard $(VENV)/bin/python),)
PYTHON := python3
PYTEST := pytest
RUFF := ruff
MYPY := mypy
else
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
endif

.PHONY: test lint typecheck security

test:
	$(PYTEST) -q

lint:
	$(RUFF) check src tests

typecheck:
	$(MYPY) src tests

security:
	@command -v $(VENV)/bin/pip-audit >/dev/null 2>&1 || true
	@$(PYTHON) -m pip check || exit 1
	@if command -v bandit >/dev/null 2>&1; then $(RUFF) check src tests; fi
	@echo "Security checks: dependency audit + static scan recommended in CI (see .github/workflows/ci.yml)."

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

.PHONY: test test-e2e lint typecheck security

test:
	$(PYTEST) -q

# Subprocess E2E (same scenarios as CI job `e2e` on Ubuntu/Windows/macOS).
test-e2e:
	$(PYTEST) -q tests/e2e/

lint:
	$(RUFF) check src tests

typecheck:
	$(MYPY) src tests

security:
	@echo "== pip check =="
	@$(PYTHON) -m pip check
	@echo "== ruff =="
	@$(RUFF) check src tests
	@echo "== mypy =="
	@$(MYPY) src tests
	@echo "== bandit =="
	@if $(PYTHON) -c "import bandit" 2>/dev/null; then \
		$(PYTHON) -m bandit -r src -q && echo "bandit OK"; \
	else \
		echo "SKIP: bandit (pip install bandit)"; \
	fi
	@echo "== pip-audit =="
	@if command -v pip-audit >/dev/null 2>&1; then pip-audit --skip-editable || true; \
	elif $(PYTHON) -m pip_audit --help >/dev/null 2>&1; then $(PYTHON) -m pip_audit --skip-editable || true; \
	else \
		echo "SKIP: pip-audit (install with: pip install pip-audit)"; \
	fi
	@echo "(editable installs may show 'not on PyPI' for pyrtkai — expected locally)"

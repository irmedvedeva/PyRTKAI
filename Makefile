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

.PHONY: test test-e2e lint typecheck security smoke-install

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

smoke-install:
	@set -e; \
	SMOKE_VENV=".venv-clean-smoke"; \
	rm -rf "$$SMOKE_VENV"; \
	python3 -m venv "$$SMOKE_VENV"; \
	. "$$SMOKE_VENV/bin/activate"; \
	python -m pip install --upgrade pip >/dev/null; \
	python -m pip install . >/dev/null; \
	CLI_VERSION=$$(pyrtkai status --json | python -c "import json,sys; d=json.load(sys.stdin); print(d['pyrtkai_version'])"); \
	IMPL_VERSION=$$(python -c "import pyrtkai; print(pyrtkai.__version__)"); \
	test "$$CLI_VERSION" = "$$IMPL_VERSION"; \
	pyrtkai init --json | python -c "import json,sys; d=json.load(sys.stdin); assert 'pyrtkai_version' in d and 'python_executable' in d"; \
	pyrtkai doctor --json > /dev/null; \
	deactivate; \
	rm -rf "$$SMOKE_VENV"; \
	echo "smoke-install OK ($$CLI_VERSION)"

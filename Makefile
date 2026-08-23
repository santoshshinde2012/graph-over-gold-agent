.PHONY: setup test lint format typecheck check demo demo-json clean

PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

setup: ## Create the venv and install the package with dev extras
	$(PY) -m venv $(VENV)
	$(BIN)/pip install -q --upgrade pip
	$(BIN)/pip install -q -e ".[dev]"

test: ## Run the test suite with coverage
	$(BIN)/pytest --cov --cov-report=term-missing

lint: ## Ruff lint + format check
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

format: ## Auto-format with ruff
	$(BIN)/ruff check --fix .
	$(BIN)/ruff format .

typecheck: ## mypy --strict on the package
	$(BIN)/mypy

check: lint typecheck test ## Everything CI runs

demo: ## Print the three-path comparison
	$(BIN)/graph-over-gold

demo-json: ## Machine-readable summary only
	$(BIN)/graph-over-gold --json

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov build dist src/*.egg-info northwind_gold.db
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

.PHONY: install dev test lint format type-check clean all

all: lint type-check test

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --tb=short --cov=medscribe --cov-report=html

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

type-check:
	mypy src/medscribe/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

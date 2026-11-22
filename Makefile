.PHONY: install test lint format demo clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest --cov=afrocross --cov-report=term-missing

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

demo:
	python scripts/run_demo.py

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov build dist src/*.egg-info

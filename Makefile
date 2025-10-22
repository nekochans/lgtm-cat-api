.PHONY: lint fix format typecheck test run

lint:
	uv run ruff check

fix:
	uv run ruff check --fix

format:
	uv run ruff format

typecheck:
	uv run mypy src/ tests/ --strict

test:
	uv run pytest -vv -s src/ tests/

run:
	uv run python src/main.py
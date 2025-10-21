.PHONY: lint fix format typecheck

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

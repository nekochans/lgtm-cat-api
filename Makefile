.PHONY: lint fix format typecheck

lint:
	uv run ruff check

fix:
	uv run ruff check --fix

format:
	uv run ruff format

typecheck:
	uv run mypy src/ --strict

.PHONY: lint fix format

lint:
	rye run ruff check

fix:
	rye run ruff check --fix

format:
	rye run ruff format

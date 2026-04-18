.PHONY: clean format lint

clean: format lint
	@echo "Code formatting and linting complete"

format:
	@echo "Formatting code with ruff..."
	uv run ruff format

lint:
	@echo "Linting code with ruff..."
	uv run ruff check --fix

run:
	python -m src.main
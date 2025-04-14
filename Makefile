# Multiple runners
# Runs linters
lint:
	make -j 2 lint-djlint lint-ruff

# Attempts to fix linting issues
# Note that djlint does not have this feature
lint-fix:
	make -j 1 lint-fix-ruff

# Runs formatters
format: 
	make -j 2 format-djlint format-ruff

# Attempts to fix formatting issues
format-fix: 
	make -j 2 format-fix-djlint format-fix-ruff

# Individual runners
lint-djlint:
	uv run djlint . --extension=html.j2 --lint

lint-ruff:
	uv run ruff check

lint-fix-ruff:
	uv run ruff check --fix

format-djlint:
	uv run djlint . --extension=html.j2 --check

format-ruff:
	uv run ruff format --check

format-fix-djlint:
	uv run djlint . --extension=html.j2 --reformat

format-fix-ruff:
	uv run ruff format
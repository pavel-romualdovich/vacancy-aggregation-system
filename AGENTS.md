## Project Snapshot
- Stack: Python 3.12+, FastAPI, PostgreSQL
- Source Root: vacancy_aggregator/ (flat layout)
- Tooling: uv, Ruff, pytest, mypy

## Commands
- Setup: uv sync
- Lint: uv run ruff check .
- Format: uv run ruff format .
- Type check: uv run mypy vacancy_aggregator

## Conventions
- Keep ruff check, ruff format and mypy green
- Use Conventional Commits for commits
- Use Google style for docstrings
- Type hints required everywhere
- Use asyncio for all I/O

## Boundaries
- Never use print for logging — use logging library
- Never use secrets directly
# Contributing to Demand Forecasting

Thanks for your interest! This guide covers how to set up the project, make changes, and submit them.

## Development Setup

```bash
git clone https://github.com/twomathematicians-code/demand-forecasting.git
cd demand-forecasting
pip install -r requirements.txt
pip install pre-commit
pre-commit install
```

## Pre-Commit Hooks

We use pre-commit to enforce code quality before every commit:

- **ruff** — Linting and import sorting
- **ruff format** — Code formatting
- **check-yaml** — Validates YAML files
- **check-toml** — Validates TOML files
- **end-of-file-fixer** — Ensures files end with newline
- **trailing-whitespace** — Removes trailing whitespace

Run manually: `pre-commit run --all-files`

## Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing

# Specific suites
pytest tests/test_models.py -v
pytest tests/test_api.py -v
```

## Code Style

- Follow existing patterns: model wrappers have `fit()`, `predict()`, `save()`, `load()`, `is_fitted`
- Config goes through Pydantic models in `src/utils/config.py`
- API endpoints use Pydantic schemas for request/response
- Database queries are parameterized in `src/db/queries.py`
- All new features need tests (target: 70%+ coverage)

## Pull Request Checklist

- [ ] Tests pass: `pytest tests/ -v`
- [ ] Coverage ≥ 60%: `pytest tests/ --cov=src --cov-fail-under=60`
- [ ] Lint passes: `ruff check src/ tests/`
- [ ] Pre-commit hooks pass: `pre-commit run --all-files`
- [ ] Update README if adding features
- [ ] Update version in `pyproject.toml`, `src/__init__.py`, `src/api/main.py`

## Architecture Decisions

- **Config-driven**: All hyperparameters live in `configs/model_config.yaml`, validated by Pydantic
- **Model wrapper pattern**: Every model implements the same interface for ensemble compatibility
- **Graceful fallback**: API never fails — returns demo data when models aren't loaded
- **Database**: asyncpg with parameterized queries, Alembic for migrations, TimescaleDB for time-series
- **Streaming**: aiokafka consumers run as FastAPI lifespan background tasks

## Questions?

Open an issue or start a discussion on GitHub.

.PHONY: install test lint run train db-migrate docker-build docker-up docker-down clean

install:
	poetry install --with dev

test:
	poetry run pytest tests/ -v

lint:
	poetry run ruff check src/ tests/

run:
	poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

train:
	poetry run python scripts/train.py

train-with-data:
	poetry run python scripts/train.py --data $(DATA)

db-migrate:
	poetry run python scripts/migrate.py

db-downgrade:
	poetry run python scripts/migrate.py --downgrade

docker-build:
	docker build -t ml-demand-forecasting:latest .

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

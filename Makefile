.PHONY: install test lint run docker-build docker-up docker-down

install:
	poetry install --with dev

test:
	poetry run pytest tests/ --cov=src -v

lint:
	poetry run black --check src/ tests/
	poetry run ruff check src/ tests/

run:
	poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -t ml-demand-forecasting:latest .

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

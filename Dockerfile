FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install poetry && poetry install --only main --no-root --no-interaction
COPY src/ src/ configs/ configs/
RUN useradd -m -r demanduser && chown -R demanduser /app
USER demanduser
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

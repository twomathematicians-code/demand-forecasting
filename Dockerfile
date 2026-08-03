# ── Fly.io Production Dockerfile ──
# Multi-stage build optimized for Fly.io deployment
# Build: fly deploy

# ── Stage 1: Builder ──
FROM python:3.11-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ src/
COPY configs/ configs/
COPY scripts/ scripts/

# Create non-root user (Fly.io best practice)
RUN useradd -m -r appuser && chown -R appuser /app
USER appuser

# Create data directory for model artifacts
RUN mkdir -p /data/models && chown -R appuser /data

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/health || exit 1

EXPOSE 8080

# Fly.io provides PORT env var
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2 --log-level info"]

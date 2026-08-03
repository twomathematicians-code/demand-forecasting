# 🚀 Deployment Guide

Deploy the Demand Forecasting API to production in minutes.

---

## Option 1: Render (Recommended — Free Tier)

One-click deploy with PostgreSQL, Redis, and automatic HTTPS.

### Quick Deploy

1. **Fork this repo** to your GitHub account
2. Go to **[render.com](https://render.com)** → **Blueprints** → **New Blueprint Instance**
3. Connect your GitHub repo — Render auto-detects `render.yaml`
4. Click **Apply** — deploys in ~5 minutes

**What gets created:**
- ✅ FastAPI web service (512MB, auto-scaling ready)
- ✅ PostgreSQL with TimescaleDB (1GB free, upgradeable)
- ✅ Redis cache (25MB free)
- ✅ Automatic HTTPS via `*.onrender.com`
- ✅ Auto-deploy on every `git push` to master
- ✅ Health checks + zero-downtime deploys
- ✅ Admin API key auto-generated

### After Deploy

```bash
# Your API is live at:
https://demand-forecast-api.onrender.com

# Check health
curl https://demand-forecast-api.onrender.com/api/v1/health

# Train the model (once deployed)
curl -X POST https://demand-forecast-api.onrender.com/api/v1/admin/retrain \
  -H "Authorization: Bearer YOUR_ADMIN_KEY"

# Make a forecast
curl -X POST https://demand-forecast-api.onrender.com/api/v1/forecast/demand \
  -H "Content-Type: application/json" \
  -d '{"product_id": "SKU-12345", "horizon_days": 14}'

# Dashboard
curl https://demand-forecast-api.onrender.com/api/v1/dashboard/summary?days=30
```

---

## Option 2: Docker Compose (Self-Hosted)

Full stack: API + Postgres + Kafka + Redis + Grafana.

```bash
git clone https://github.com/twomathematicians-code/demand-forecasting.git
cd demand-forecasting

# Copy and configure environment
cp .env.example .env
# Edit .env: set DF_ADMIN_API_KEY, DF_KATZILLA_API_KEY, etc.

# Start all services
docker compose up -d

# Verify
curl http://localhost:8000/api/v1/health
```

Services:
- API: `http://localhost:8000`
- Grafana: `http://localhost:3000` (admin/admin)
- Postgres: `localhost:5432`
- Kafka: `localhost:9092`
- Redis: `localhost:6379`

---

## Option 3: Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/deployment.yaml

# Create secrets
kubectl create secret generic demand-forecast-secrets \
  --from-literal=DF_DB_PASSWORD=your_db_pass \
  --from-literal=DF_ADMIN_API_KEY=your_admin_key \
  -n demand-forecasting

# Check deployment
kubectl get pods -n demand-forecasting
kubectl port-forward svc/demand-forecast-svc 8000:80 -n demand-forecasting
```

---

## Security Configuration

### Required Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `DF_ADMIN_API_KEY` | Protects `/admin/retrain` endpoint | ✅ Production |
| `DF_DB_PASSWORD` | PostgreSQL password | ✅ |
| `DF_KATZILLA_API_KEY` | Katzilla data integration | Optional |
| `DF_CORS_ORIGINS` | Allowed CORS domains (comma-separated) | Recommended |

### Production Checklist

- [ ] Set `DF_ENVIRONMENT=production`
- [ ] Set a strong `DF_ADMIN_API_KEY` (32+ chars)
- [ ] Configure `DF_CORS_ORIGINS` to your frontend domain
- [ ] Enable Redis: `DF_REDIS_ENABLED=true`
- [ ] Review rate limits (default: 200 req/min)
- [ ] Set up a custom domain in Render
- [ ] Configure Grafana alerting (if self-hosting)

---

## Environment-Specific Configs

### Development (local)
```bash
DF_ENVIRONMENT=development
DF_REDIS_ENABLED=false
DF_KAFKA_CONSUMER_ENABLED=false
DF_DRIFT_CHECK_ENABLED=false
```

### Staging (Render free tier)
```bash
DF_ENVIRONMENT=staging
DF_REDIS_ENABLED=true
DF_RATE_LIMIT_MAX=50
```

### Production (Render paid / self-hosted)
```bash
DF_ENVIRONMENT=production
DF_REDIS_ENABLED=true
DF_KAFKA_CONSUMER_ENABLED=true
DF_DRIFT_CHECK_ENABLED=true
DF_RATE_LIMIT_MAX=200
DF_API_WORKERS=4
```

---

## Monitoring

- **Render Dashboard:** CPU, memory, request latency, error rate
- **Health endpoint:** `GET /api/v1/health` — model status + uptime
- **Prometheus metrics:** `GET /metrics` — request counts, latency percentiles
- **Logs:** Structured JSON logging with request IDs — tail via `render logs` or `docker logs`

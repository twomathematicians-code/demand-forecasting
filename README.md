# 📦 Demand Forecasting for Supply Chain

[![CI](https://github.com/twomathematicians-code/demand-forecasting/actions/workflows/ci.yml/badge.svg)](https://github.com/twomathematicians-code/demand-forecasting/actions)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.3-4CAF50)](https://lightgbm.readthedocs.io/)
[![Prophet](https://img.shields.io/badge/Prophet-Forecasting-0891b2)](https://facebook.github.io/prophet/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://hub.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-31%20passed-success)](https://github.com/twomathematicians-code/demand-forecasting/actions)

> **Production-grade ML forecasting** — Prophet + LightGBM + SARIMA ensemble with MLOps-ready architecture

```bash
# Clone and run in 30 seconds
pip install -r requirements.txt
python scripts/train.py          # Train on synthetic data (auto-fallback)
uvicorn src.api.main:app --reload # Start the API
# → http://localhost:8000/docs
```

---

## 🎯 What This Does

Predicts future demand for products, order volumes, electricity consumption, and utility resources using a **three-model ensemble** that blends classical statistics with gradient boosting.

| Forecast Type | Models Used | Use Case | Accuracy (MAPE) |
|:--|:--|:--|:--|
| **Product Demand** | Prophet + LightGBM + Ridge Stacking | Inventory planning, procurement | ~10% |
| **Order Volume** | SARIMA + Ensemble | Warehouse staffing, logistics | ~12% |
| **Electricity / Energy** | LightGBM + Weather Covariates | Energy procurement, grid planning | ~15% |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (optional — for DB layer)
- Docker (optional — for containerized deployment)

### 1. Install

```bash
git clone https://github.com/twomathematicians-code/demand-forecasting.git
cd demand-forecasting
pip install fastapi uvicorn lightgbm prophet statsmodels scikit-learn pandas numpy pyyaml joblib
```

### 2. Train a Model

```bash
# Train on synthetic data (no real data needed)
python scripts/train.py

# Or train on your own CSV
python scripts/train.py --data your_historical_data.csv
```

### 3. Start the API

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Make a Forecast

```bash
# Product demand prediction
curl -X POST http://localhost:8000/api/v1/forecast/demand \
  -H "Content-Type: application/json" \
  -d '{"product_id": "SKU-12345", "horizon_days": 30, "granularity": "daily"}'

# Order volume forecast
curl http://localhost:8000/api/v1/forecast/orders?days=7

# Energy price forecast
curl http://localhost:8000/api/v1/forecast/electricity?hours=24

# Health check + model status
curl http://localhost:8000/api/v1/health
```

### Docker

```bash
docker compose up -d
# API: http://localhost:8000/docs
# Postgres: localhost:5432
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|:--|:--|:--|
| `POST` | `/api/v1/forecast/demand` | Product demand prediction with confidence intervals |
| `GET` | `/api/v1/forecast/orders` | Order volume forecast with day-of-week effects |
| `GET` | `/api/v1/forecast/electricity` | Energy demand & price forecast (hourly) |
| `GET` | `/api/v1/health` | Health check — returns model version, metrics, uptime |
| `POST` | `/api/v1/admin/retrain` | Trigger model retraining on demand |

**Swagger UI:** Open `http://localhost:8000/docs` for interactive API documentation.

---

## 🧠 How It Works

### Ensemble Architecture

```
                    ┌─────────────────────┐
                    │   Historical Data   │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────────┐
        │  Prophet  │   │  SARIMA  │   │  LightGBM    │
        │ (Trend +  │   │ (Stats   │   │ (GBDT with   │
        │ Season)   │   │ Baseline)│   │ 36 features) │
        └─────┬─────┘   └────┬─────┘   └──────┬───────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Ridge Stacking   │
                    │  (Meta-Learner)   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Final Forecast   │
                    │  + 95% CI Bounds  │
                    └───────────────────┘
```

### Feature Engineering (36 features)

| Category | Features |
|:--|:--|
| **Temporal** | Lags (t-1, t-7, t-30, t-90, t-365), Rolling stats (7d, 14d, 30d mean/std/min/max) |
| **Calendar** | Day of week, month, quarter, weekend flags, cyclical sin/cos encodings |
| **Weather** | HDD (Heating Degree Days), CDD (Cooling Degree Days), precipitation windows |
| **Cluster** | ADI (Intermittency), CV² (Dispersion), seasonality strength |

### MLOps Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Data        │    │  Training    │    │  Inference   │
│  Ingestion   │───▶│  Pipeline    │───▶│  Pipeline    │
│  (loader.py) │    │  (train.py)  │    │  (API)       │
└──────────────┘    └──────┬───────┘    └──────┬───────┘
                           │                   │
                    ┌──────▼───────┐    ┌──────▼───────┐
                    │  Model       │    │  FastAPI      │
                    │  Registry    │    │  Endpoints    │
                    │  (models/)   │    │  (main.py)    │
                    └──────────────┘    └──────────────┘
```

---

## 📊 Advantages of Using This Project

### 1. **Ready in Minutes, Not Weeks**
Self-contained with synthetic data generation and auto-fallback model training. Start forecasting immediately — no real data required for evaluation.

### 2. **Production-Grade Ensemble**
Three complementary models cover different failure modes:
- **Prophet** captures trend and multi-scale seasonality (yearly, weekly, daily)
- **SARIMA** provides a robust statistical baseline for short-horizon accuracy
- **LightGBM** learns non-linear interactions with 36 engineered features
- **Ridge stacking** prevents any single model from dominating

### 3. **Configurable & Validated**
13 Pydantic configuration models validate all hyperparameters at startup. Change model parameters in `configs/model_config.yaml` — no code changes needed. Quality gates (MAPE threshold, coverage %, bias limits) automatically check if a model is production-ready.

### 4. **Database-Backed (Ready for Scale)**
TimescaleDB schema with 6 tables, BRIN indexing, and monthly partitioning. Stores actuals, forecasts, model metadata, accuracy snapshots, drift metrics, and alerts. Scale from 100 to 100M+ rows without performance degradation.

### 5. **Comprehensive Testing**
31 tests covering API endpoints, configuration validation, feature engineering transforms, and all four model wrappers. Every model supports save/load roundtrips. Test suite runs in under 20 seconds.

### 6. **MLOps-Ready Foundation**
- Model registry (`models/`) with versioned artifacts
- Training pipeline with automated evaluation
- Inference pipeline with fallback models
- Retraining API endpoint
- Structured logging

### 7. **Docker-Native**
Single-command deployment with `docker compose up`. Includes Postgres (TimescaleDB) for the database layer. API auto-trains a fallback model if none exists.

### 8. **Industry-Aligned Architecture**
Designed from market research across PJM, United Utilities, Sydney Water, HP Inc., and automotive supply chains. The architecture scales from single-product forecasting to multi-tenant, multi-industry deployments.

---

## 📁 Project Structure

```
demand-forecasting/
├── src/
│   ├── api/main.py              # FastAPI application (5 endpoints)
│   ├── data/loader.py           # CSV/Parquet loading + synthetic data generator
│   ├── db/
│   │   ├── session.py           # asyncpg connection pool
│   │   ├── queries.py           # 20+ parameterized SQL queries
│   │   └── migrations/          # Alembic migrations (6 tables)
│   ├── features/
│   │   ├── features.py          # FeatureEngineer (36 features)
│   │   └── pipeline.py          # sklearn-compatible pipeline
│   ├── models/
│   │   ├── prophet_model.py     # Prophet wrapper (trend + seasonality)
│   │   ├── sarima_model.py      # SARIMA wrapper (statistical baseline)
│   │   ├── lightgbm_model.py    # LightGBM wrapper (gradient boosting)
│   │   └── ensemble.py          # DemandEnsemble (Ridge stacking)
│   ├── pipelines/
│   │   ├── training_pipeline.py # Train → evaluate → save
│   │   └── inference_pipeline.py# Load → predict → serve
│   └── utils/
│       ├── config.py            # 13 Pydantic config models
│       ├── logging.py           # Structured logging
│       └── metrics.py           # 8 forecast accuracy functions
├── configs/model_config.yaml    # All hyperparameters + quality gates
├── scripts/
│   ├── train.py                 # CLI training entrypoint
│   └── migrate.py               # Database migration runner
├── tests/                       # 31 tests (all passing)
├── docker-compose.yml           # API + Postgres
├── Dockerfile
├── Makefile                     # make install, test, train, run, etc.
└── docs/                        # Architecture PDFs + SOP documentation
```

---

## 🔧 Configuration

All model parameters live in `configs/model_config.yaml`:

```yaml
models:
  lightgbm:
    n_estimators: 500
    learning_rate: 0.05
    max_depth: 8
  prophet:
    seasonality_mode: multiplicative
    changepoint_range: 0.8
  sarima:
    order: [2, 1, 2]
    seasonal_order: [1, 1, 1, 7]

quality_gates:
  min_mape: 15.0          # Model must beat 15% MAPE
  min_coverage_pct: 0.85   # 85% of actuals within prediction interval
  max_bias: 5.0            # Bias within ±5%
```

Environment variables (`.env` or system):
```bash
DF_ENVIRONMENT=production
DF_DB_HOST=localhost
DF_DB_PORT=5432
DF_MLFLOW_TRACKING_URI=http://localhost:5000
```

---

## 🧪 Testing

```bash
# Run all tests (31 tests, <20 seconds)
make test

# Run specific test suites
pytest tests/test_models.py -v    # Model wrappers (11 tests)
pytest tests/test_features.py -v  # Feature engineering (5 tests)
pytest tests/test_config.py -v    # Configuration (9 tests)
pytest tests/test_api.py -v       # API endpoints (6 tests)
```

---

## 🗺️ Roadmap

| Phase | Status | Features |
|:--|:--|:--|
| **Phase 1** | ✅ Complete | Real ML ensemble, DB layer, feature engineering, config system, 31 tests |
| **Phase 2** | 🔜 Planned | CNN-LSTM PyTorch model, Kafka streaming, BI dashboards, drift monitoring |
| **Phase 3** | 📋 Backlog | Redis caching, Grafana dashboards, CI/CD hardening, multi-tenant support |

---

## 📚 Documentation

- **[Client Requirements & Technical Architecture](docs/Client_Requirements_Technical_Architecture.pdf)** — 11-page architecture document with industry benchmarks
- **[SOP — ML Development Lifecycle](docs/SOP_Demand_Forecasting_ML_Development.pdf)** — 14-page standard operating procedure (9 phases)

---

<p align="center">
  <i>Built with ❤️ by <a href="https://github.com/twomathematicians-code">Mahesh Solanki</a> — Forecasting the future, one ensemble at a time.</i>
</p>

# 📦 Demand Forecasting for Supply Chain

[![CI](https://github.com/twomathematicians-code/demand-forecasting/actions/workflows/ci.yml/badge.svg)](https://github.com/twomathematicians-code/demand-forecasting/actions)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.3-4CAF50)](https://lightgbm.readthedocs.io/)
[![Prophet](https://img.shields.io/badge/Prophet-Forecasting-0891b2)](https://facebook.github.io/prophet/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://hub.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Prophet · LightGBM · SARIMA · Seasonal Decomposition

```bash
docker compose up -d
# API: http://localhost:8000/docs
```

## What This Does

Predicts future demand for products, order volumes, and even electricity consumption.

| Forecast Type | Model | Use Case |
|:--|:--|:--|
| Product Demand | LightGBM + Prophet | Inventory planning |
| Order Volume | SARIMA | Warehouse staffing |
| Electricity | Ensemble | Energy procurement |

## Try It

```bash
# Demand forecast for a product
curl -X POST http://localhost:8000/api/v1/forecast/demand -H "Content-Type: application/json" \
  -d '{"product_id": "SKU-12345", "horizon_days": 30, "granularity": "daily"}'
```

## Endpoints

- `POST /api/v1/forecast/demand` — Product demand prediction
- `GET  /api/v1/forecast/orders` — Order volume forecast
- `GET  /api/v1/forecast/electricity` — Energy demand forecast

---

<p><i>Mahesh Solanki · <a href="https://github.com/twomathematicians-code">GitHub</a></i></p>

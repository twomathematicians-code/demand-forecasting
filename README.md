# 📦 Demand Forecasting for Supply Chain

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

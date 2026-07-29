# 📊 ML Demand Forecasting

[![CI/CD](https://github.com/twomathematicians-code/ml-demand-forecasting/actions/workflows/ci.yml/badge.svg)](https://github.com/twomathematicians-code/ml-demand-forecasting/actions)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://hub.docker.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-Ready-3377B0)](https://xgboost.readthedocs.io/)

**Production demand forecasting API: product demand, sales prediction, electricity price, and order volume — ensemble of LightGBM, Prophet, and statistical models with automated hyperparameter tuning.**

## 🎯 Forecasting Modules

| Module | Algorithm | Horizon |
|---|---|---|
| **Product Demand** | LightGBM + Feature Engineering | 30/60/90 day |
| **Sales Prediction** | Prophet + Holiday Effects | Weekly/Monthly |
| **Electricity Price** | XGBoost + Weather Features | 24h ahead |
| **Order Volume** | Ensemble (LGBM + ARIMA) | Daily/Weekly |

## 🚀 Quick Start

```bash
git clone https://github.com/twomathematicians-code/ml-demand-forecasting.git
cd ml-demand-forecasting
docker-compose up --build
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/forecast/demand` | Product demand forecast |
| `POST` | `/api/v1/forecast/sales` | Sales prediction |
| `POST` | `/api/v1/forecast/electricity` | Electricity price forecast |
| `POST` | `/api/v1/forecast/orders` | Order volume prediction |
| `GET` | `/api/v1/health` | Health check |

## 👤 Author

**Mahesh Solanki** — [LinkedIn](https://linkedin.com/in/maheshsolanki-16b9a6a5) | [GitHub](https://github.com/twomathematicians-code)

"""Dashboard API routes — BI aggregation endpoints for demand forecasting.

Mounted as a FastAPI router at /api/v1/dashboard.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.db.queries import (
    DASHBOARD_SUMMARY,
    DASHBOARD_TOP_PRODUCTS,
    DASHBOARD_TREND,
    FORECAST_VS_ACTUAL,
    DASHBOARD_ACCURACY_TREND,
    GET_ACTIVE_ALERTS,
)
from src.db.session import get_connection
from src.cache.redis_cache import cached

router = APIRouter(prefix="/api/v1/dashboard", tags=["📊 Dashboard"])
log = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────

def _choose_rollup_table(days: int) -> str:
    """Select the right aggregation table based on requested time range."""
    if days <= 7:
        return "actuals_daily_rollup"
    elif days <= 60:
        return "actuals_daily_rollup"
    elif days <= 365:
        return "actuals_weekly_rollup"
    else:
        return "actuals_monthly_rollup"


# ── Endpoints ────────────────────────────────────────────

@router.get("/summary")
async def dashboard_summary(
    days: int = Query(default=30, ge=1, le=730, description="Lookback window in days"),
):
    """Aggregated KPI summary: total demand, revenue, avg daily demand, active products."""
    end = date.today()
    start = end - timedelta(days=days)

    try:
        async with get_connection() as conn:
            row = await conn.fetchrow(DASHBOARD_SUMMARY, start, end)
            top = await conn.fetch(DASHBOARD_TOP_PRODUCTS, start, end, 10)
    except Exception as e:
        log.warning("Dashboard summary unavailable (DB may not be running): %s", e)
        return {
            "total_demand": 0,
            "total_revenue": 0,
            "avg_daily_demand": 0,
            "active_products": 0,
            "top_products": [],
            "period": {"start": str(start), "end": str(end), "days": days},
        }

    return {
        "total_demand": float(row["total_demand"]) if row else 0,
        "total_revenue": float(row["total_revenue"]) if row else 0,
        "avg_daily_demand": float(row["avg_daily_demand"]) if row else 0,
        "active_products": row["active_products"] if row else 0,
        "top_products": [
            {
                "product_id": r["product_id"],
                "total_qty": float(r["total_qty"]),
                "total_revenue": float(r["total_revenue"]),
            }
            for r in (top or [])
        ],
        "period": {"start": str(start), "end": str(end), "days": days},
    }


@router.get("/trends")
async def dashboard_trends(
    days: int = Query(default=90, ge=7, le=730, description="Lookback window in days"),
    metric: str = Query(default="quantity_sold", pattern="^(quantity_sold|revenue)$"),
):
    """Time-series trend data for BI charts. Uses adaptive rollup for performance."""
    end = date.today()
    start = end - timedelta(days=days)
    table = _choose_rollup_table(days)

    try:
        async with get_connection() as conn:
            rows = await conn.fetch(
                DASHBOARD_TREND.format(table), start, end
            )
    except Exception as e:
        log.warning("Dashboard trends unavailable: %s", e)
        return {"series": [], "period": {"start": str(start), "end": str(end)}}

    series = []
    for r in (rows or []):
        series.append({
            "date": str(r["bucket"].date()),
            "quantity_sold": float(r["total_qty"]),
            "revenue": float(r["total_revenue"]),
            "avg_daily": float(r["avg_qty"]),
        })

    return {
        "series": series,
        "period": {"start": str(start), "end": str(end), "days": days},
        "granularity": "daily" if days <= 60 else "weekly" if days <= 365 else "monthly",
    }


@router.get("/accuracy")
async def forecast_accuracy(
    model_id: int = Query(default=1, ge=1, description="Model ID from model_metadata"),
    days: int = Query(default=90, ge=7, le=365, description="Lookback window"),
):
    """Forecast accuracy trend over time: MAPE, RMSE, bias."""
    end = date.today()
    start = end - timedelta(days=days)

    try:
        async with get_connection() as conn:
            rows = await conn.fetch(DASHBOARD_ACCURACY_TREND, model_id, start, 90)
    except Exception as e:
        log.warning("Accuracy data unavailable: %s", e)
        return {"model_id": model_id, "history": []}

    return {
        "model_id": model_id,
        "history": [
            {
                "date": str(r["evaluation_date"]),
                "mae": float(r["mae"]) if r["mae"] else None,
                "rmse": float(r["rmse"]) if r["rmse"] else None,
                "mape": float(r["mape"]) if r["mape"] else None,
                "bias": float(r["bias"]) if r["bias"] else None,
                "wmape": float(r["wmape"]) if r["wmape"] else None,
            }
            for r in (rows or [])
        ],
    }


@router.get("/forecast-vs-actual")
async def forecast_vs_actual(
    model_id: int = Query(default=1, ge=1),
    product_id: Optional[int] = Query(default=None),
    days: int = Query(default=30, ge=1, le=90),
):
    """Compare forecasts against actuals for backtesting visualization."""
    end = date.today()
    start = end - timedelta(days=days)

    try:
        async with get_connection() as conn:
            rows = await conn.fetch(FORECAST_VS_ACTUAL, model_id, start, end, product_id)
    except Exception as e:
        log.warning("Forecast-vs-actual unavailable: %s", e)
        return {"model_id": model_id, "points": []}

    return {
        "model_id": model_id,
        "points": [
            {
                "date": str(r["target_date"]),
                "predicted": float(r["predicted_qty"]),
                "actual": float(r["actual_qty"]),
                "error": float(r["error"]),
                "lower_bound": float(r["yhat_lower"]) if r["yhat_lower"] else None,
                "upper_bound": float(r["yhat_upper"]) if r["yhat_upper"] else None,
            }
            for r in (rows or [])
        ],
    }


@router.get("/alerts")
async def active_alerts():
    """List all unacknowledged monitoring alerts."""
    try:
        async with get_connection() as conn:
            rows = await conn.fetch(GET_ACTIVE_ALERTS)
    except Exception as e:
        log.warning("Alerts unavailable: %s", e)
        return {"alerts": []}

    return {
        "alerts": [
            {
                "alert_id": r["alert_id"],
                "model_id": r["model_id"],
                "type": r["alert_type"],
                "severity": r["severity"],
                "message": r["message"],
                "created_at": str(r["created_at"]),
            }
            for r in (rows or [])
        ],
    }

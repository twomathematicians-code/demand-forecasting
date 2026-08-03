"""API integration tests — uses real model pipeline with synthetic data.

Tests run against a FastAPI TestClient with a model that's auto-trained
on synthetic data at startup (via the lifespan handler).
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import app


@pytest_asyncio.fixture
async def client():
    """Create an async test client. The lifespan handler will auto-train a fallback model."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    """Health check should return model status."""
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "model_version" in data


@pytest.mark.asyncio
async def test_demand_forecast(client):
    """POST /forecast/demand should return a valid forecast."""
    r = await client.post(
        "/api/v1/forecast/demand",
        json={"product_id": "SKU-TEST-1", "horizon_days": 14, "granularity": "daily"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["product_id"] == "SKU-TEST-1"
    assert len(data["forecast"]) == 14
    assert data["horizon_days"] == 14
    # Check forecast point structure
    point = data["forecast"][0]
    assert "date" in point
    assert "predicted_demand" in point
    assert "lower_bound" in point
    assert "upper_bound" in point
    assert "trend_component" in point
    assert "seasonal_component" in point
    # Check response metadata
    assert "total_predicted_demand" in data
    assert "avg_daily_demand" in data
    assert data["trend"] in ("increasing", "decreasing", "stable")
    assert len(data["model_ensemble"]) == 3


@pytest.mark.asyncio
async def test_demand_forecast_defaults(client):
    """Forecast with defaults should still work."""
    r = await client.post(
        "/api/v1/forecast/demand",
        json={"product_id": "SKU-DEFAULT"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["forecast"]) == 30  # default horizon


@pytest.mark.asyncio
async def test_orders(client):
    """GET /forecast/orders should return order predictions."""
    r = await client.get("/api/v1/forecast/orders?days=7")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 7
    assert "predicted_orders" in data[0]
    assert "day_of_week" in data[0]
    assert "confidence_interval" in data[0]


@pytest.mark.asyncio
async def test_electricity(client):
    """GET /forecast/electricity should return price forecast points."""
    r = await client.get("/api/v1/forecast/electricity?hours=24")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 24
    assert "price_per_kwh" in data[0]
    assert "demand_mw" in data[0]


@pytest.mark.asyncio
async def test_forecast_validation(client):
    """Invalid horizon should be rejected."""
    r = await client.post(
        "/api/v1/forecast/demand",
        json={"product_id": "SKU-1", "horizon_days": 400},  # > 365
    )
    assert r.status_code == 422  # validation error

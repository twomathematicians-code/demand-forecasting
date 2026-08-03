"""Tests for dashboard API routes."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_summary(client):
    r = await client.get("/api/v1/dashboard/summary?days=30")
    assert r.status_code == 200
    data = r.json()
    assert "total_demand" in data
    assert "total_revenue" in data
    assert "active_products" in data
    assert "period" in data


@pytest.mark.asyncio
async def test_trends(client):
    r = await client.get("/api/v1/dashboard/trends?days=90")
    assert r.status_code == 200
    data = r.json()
    assert "series" in data
    assert "period" in data


@pytest.mark.asyncio
async def test_accuracy(client):
    r = await client.get("/api/v1/dashboard/accuracy?model_id=1&days=90")
    assert r.status_code == 200
    data = r.json()
    assert data["model_id"] == 1
    assert "history" in data


@pytest.mark.asyncio
async def test_forecast_vs_actual(client):
    r = await client.get("/api/v1/dashboard/forecast-vs-actual?model_id=1&days=30")
    assert r.status_code == 200
    data = r.json()
    assert "model_id" in data
    assert "points" in data


@pytest.mark.asyncio
async def test_alerts(client):
    r = await client.get("/api/v1/dashboard/alerts")
    assert r.status_code == 200
    data = r.json()
    assert "alerts" in data

import pytest
from httpx import ASGITransport, AsyncClient
from src.api.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_demand_forecast(client):
    r = await client.post("/api/v1/forecast/demand", json={"product_id": "SKU-1", "horizon_days": 14})
    assert r.status_code == 200
    d = r.json()
    assert len(d["forecast"]) == 14
    assert d["product_id"] == "SKU-1"

@pytest.mark.asyncio
async def test_orders(client):
    r = await client.get("/api/v1/forecast/orders?days=7")
    assert r.status_code == 200
    assert len(r.json()) == 7

@pytest.mark.asyncio
async def test_electricity(client):
    r = await client.get("/api/v1/forecast/electricity?hours=24")
    assert r.status_code == 200
    assert all("price_per_kwh" in p for p in r.json())

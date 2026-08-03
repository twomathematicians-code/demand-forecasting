"""Tests for Katzilla API client."""

import pytest


class TestKatzillaClient:
    def test_init_without_key(self):
        from src.data.katzilla import KatzillaClient
        client = KatzillaClient(api_key="")
        assert not client.is_configured

    def test_init_with_key(self):
        from src.data.katzilla import KatzillaClient
        client = KatzillaClient(api_key="kz_test_key_123")
        assert client.is_configured

    def test_energy_tickers_list(self):
        from src.data.katzilla import ENERGY_TICKERS
        assert len(ENERGY_TICKERS) >= 10
        assert "XOM" in ENERGY_TICKERS
        assert "NEE" in ENERGY_TICKERS

    def test_extract_indicators_empty(self):
        from src.data.katzilla import KatzillaClient
        indicators = KatzillaClient.extract_energy_indicators({})
        assert indicators["energy_filing_count"] == 0
        assert indicators["energy_tickers_filed"] == 0

    def test_extract_indicators_with_data(self):
        from src.data.katzilla import KatzillaClient
        data = {
            "XOM": {
                "data": [
                    {"filing_type": "10-K", "filed_at": "2025-02-15T00:00:00Z"},
                    {"filing_type": "10-Q", "filed_at": "2025-05-01T00:00:00Z"},
                ]
            },
            "NEE": {
                "data": [
                    {"filing_type": "8-K", "filed_at": "2025-06-10T00:00:00Z"},
                ]
            },
        }
        indicators = KatzillaClient.extract_energy_indicators(data)
        assert indicators["energy_filing_count"] == 3
        assert indicators["energy_tickers_filed"] == 2
        assert indicators["latest_filing_date"] is not None
        assert "XOM" in indicators["ticker_details"]
        assert indicators["ticker_details"]["XOM"]["count"] == 2

    def test_to_feature_dict(self):
        from src.data.katzilla import KatzillaClient
        indicators = {
            "energy_filing_count": 5,
            "energy_tickers_filed": 3,
            "latest_filing_date": "2025-06-01T00:00:00+00:00",
        }
        features = KatzillaClient.to_feature_dict(indicators)
        assert features["katzilla_energy_filing_count"] == 5.0
        assert features["katzilla_energy_tickers_filed"] == 3.0
        assert "katzilla_days_since_latest_filing" in features

    def test_get_filings_without_key(self):
        """get_filings should return empty without making a request when no key."""
        import asyncio
        from src.data.katzilla import KatzillaClient
        client = KatzillaClient(api_key="")
        result = asyncio.run(client.get_filings("XOM", limit=3))
        assert result == {"data": [], "citation": {}}

    def test_singleton(self):
        from src.data.katzilla import get_katzilla_client
        c1 = get_katzilla_client()
        c2 = get_katzilla_client()
        assert c1 is c2

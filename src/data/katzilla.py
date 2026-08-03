"""Katzilla API client — energy sector SEC filings data for demand forecasting.

Katzilla provides primary-source SEC filing data. We use it to pull
energy sector financials, production volumes, and market signals
as external regressors for demand forecasting models.

Usage:
    client = KatzillaClient(api_key="kz_live_...")
    filings = await client.get_energy_filings(ticker="XOM", limit=10)
    indicators = client.extract_energy_indicators(filings)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

log = logging.getLogger(__name__)

# Major energy sector tickers — upstream, midstream, downstream, utilities
ENERGY_TICKERS = [
    # Integrated Oil & Gas
    "XOM",   # ExxonMobil
    "CVX",   # Chevron
    "BP",    # BP
    "SHEL",  # Shell
    "TTE",   # TotalEnergies
    # Utilities
    "DUK",   # Duke Energy
    "NEE",   # NextEra Energy
    "SO",    # Southern Company
    "D",     # Dominion Energy
    "AEP",   # American Electric Power
    # Renewables
    "ENPH",  # Enphase Energy
    "FSLR",  # First Solar
    # Natural Gas
    "LNG",   # Cheniere Energy
    "KMI",   # Kinder Morgan
]

KATZILLA_BASE_URL = "https://api.katzilla.dev"


class KatzillaClient:
    """Async client for Katzilla SEC filings API.

    Args:
        api_key: Katzilla API key (kz_live_...). Falls back to DF_KATZILLA_API_KEY env var.
        base_url: API base URL.
    """

    def __init__(self, api_key: str | None = None, base_url: str = KATZILLA_BASE_URL):
        self.api_key = api_key or os.getenv("DF_KATZILLA_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-API-Key": self.api_key,
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ── SEC Filings ──────────────────────────────────────

    async def get_filings(
        self,
        ticker: str,
        limit: int = 5,
        filing_type: str | None = None,
    ) -> dict[str, Any]:
        """Fetch SEC filings for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'XOM', 'CVX').
            limit: Max filings to return.
            filing_type: Optional filter: '10-K', '10-Q', '8-K', etc.

        Returns:
            Dict with 'data' (list of filings) and 'citation' (source metadata).
        """
        if not self.is_configured:
            log.warning("Katzilla API key not configured. Skipping %s", ticker)
            return {"data": [], "citation": {}}

        client = await self._get_client()
        params: dict[str, Any] = {"ticker": ticker.upper(), "limit": limit}
        if filing_type:
            params["filing_type"] = filing_type

        try:
            response = await client.get("/v1/sec/filings", params=params)
            response.raise_for_status()
            data = response.json()
            log.info("Katzilla: %d filings for %s", len(data.get("data", [])), ticker)
            return data
        except httpx.HTTPStatusError as e:
            log.error("Katzilla API error for %s: %s", ticker, e)
            return {"data": [], "citation": {}, "error": str(e)}
        except Exception as e:
            log.error("Katzilla request failed for %s: %s", ticker, e)
            return {"data": [], "citation": {}, "error": str(e)}

    async def get_energy_filings(
        self,
        tickers: list[str] | None = None,
        limit_per_ticker: int = 5,
    ) -> dict[str, Any]:
        """Fetch filings for multiple energy sector tickers.

        Args:
            tickers: List of ticker symbols. Defaults to ENERGY_TICKERS.
            limit_per_ticker: Filings per ticker.

        Returns:
            Dict mapping ticker → filings response.
        """
        if tickers is None:
            tickers = ENERGY_TICKERS

        results = {}
        for ticker in tickers:
            results[ticker] = await self.get_filings(ticker, limit=limit_per_ticker)

        total = sum(len(r.get("data", [])) for r in results.values())
        log.info("Katzilla: pulled %d total filings across %d energy tickers", total, len(tickers))
        return results

    # ── Energy Indicator Extraction ───────────────────────

    @staticmethod
    def extract_energy_indicators(filings_data: dict[str, Any]) -> dict[str, Any]:
        """Extract demand-relevant indicators from energy sector filings.

        Parses filing metadata to build features like:
        - Filing frequency (proxy for reporting intensity)
        - Recent filing count (proxy for corporate activity)
        - Period end dates (for temporal alignment)

        Args:
            filings_data: Output from get_energy_filings().

        Returns:
            Dict with indicator values keyed by ticker.
        """
        indicators: dict[str, Any] = {
            "energy_filing_count": 0,
            "energy_tickers_filed": 0,
            "latest_filing_date": None,
            "ticker_details": {},
        }
        _latest_dt: datetime | None = None  # Track max datetime for comparison

        for ticker, response in filings_data.items():
            filings = response.get("data", [])
            if not filings:
                continue

            indicators["energy_filing_count"] += len(filings)
            indicators["energy_tickers_filed"] += 1

            dates = []
            for f in filings:
                filed_at = f.get("filed_at") or f.get("filing_date") or f.get("date")
                if filed_at:
                    try:
                        dates.append(datetime.fromisoformat(str(filed_at).replace("Z", "+00:00")))
                    except (ValueError, TypeError):
                        pass

            if dates:
                ticker_latest = max(dates)
                if _latest_dt is None or ticker_latest > _latest_dt:
                    _latest_dt = ticker_latest
                    indicators["latest_filing_date"] = _latest_dt.isoformat()

            indicators["ticker_details"][ticker] = {
                "count": len(filings),
                "types": list({f.get("filing_type", f.get("type", "unknown")) for f in filings}),
            }

        return indicators

    @staticmethod
    def to_feature_dict(indicators: dict[str, Any]) -> dict[str, float]:
        """Convert extracted indicators to a flat feature dict for model input.

        Returns a dict of float values that can be merged into the feature DataFrame.
        """
        features: dict[str, float] = {}

        features["katzilla_energy_filing_count"] = float(indicators.get("energy_filing_count", 0))
        features["katzilla_energy_tickers_filed"] = float(indicators.get("energy_tickers_filed", 0))

        # Days since latest filing (if available)
        latest = indicators.get("latest_filing_date")
        if latest:
            try:
                latest_dt = datetime.fromisoformat(str(latest).replace("Z", "+00:00"))
                days_ago = (datetime.now(timezone.utc) - latest_dt).days
                features["katzilla_days_since_latest_filing"] = float(days_ago)
            except (ValueError, TypeError):
                features["katzilla_days_since_latest_filing"] = -1.0
        else:
            features["katzilla_days_since_latest_filing"] = -1.0

        return features


# ── Singleton ────────────────────────────────────────────

_client: KatzillaClient | None = None


def get_katzilla_client() -> KatzillaClient:
    global _client
    if _client is None:
        api_key = os.getenv("DF_KATZILLA_API_KEY", "")
        _client = KatzillaClient(api_key=api_key)
    return _client

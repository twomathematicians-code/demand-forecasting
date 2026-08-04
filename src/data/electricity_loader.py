"""HuggingFace electricity dataset loader.

Loads the Brazilian hourly electricity demand dataset from HuggingFace:
    SamuelM0422/Hourly-Electricity-Demand-Brazil-Dataset

Columns: id_subsistema, nom_subsistema, din_instante, val_cargaenergiahomwmed
Regions: N (Norte), NE (Nordeste), S (Sul), SE (Sudeste)

The dataset is loaded once and cached in-memory for all subsequent requests.
"""

from __future__ import annotations

import logging
from threading import Lock
from typing import ClassVar

import numpy as np
import pandas as pd

log = logging.getLogger("demand.electricity")

# Dataset config
DATASET_ID = "SamuelM0422/Hourly-Electricity-Demand-Brazil-Dataset"

# Friendly names for regions
REGION_NAMES: dict[str, str] = {
    "N": "Norte",
    "NE": "Nordeste",
    "S": "Sul",
    "SE": "Sudeste",
}

# Colors for each region (used by dashboard)
REGION_COLORS: dict[str, str] = {
    "N": "#22c55e",
    "NE": "#eab308",
    "S": "#3b82f6",
    "SE": "#a855f7",
}


class ElectricityDataLoader:
    """Singleton loader for HuggingFace electricity demand dataset.

    Usage:
        loader = ElectricityDataLoader()
        df = await loader.get_data()      # loads on first call, cached after
        df_region = loader.get_region("SE")
        summary = loader.get_summary()
    """

    _instance: ClassVar["ElectricityDataLoader | None"] = None
    _lock: ClassVar[Lock] = Lock()
    _data: pd.DataFrame | None = None
    _loaded: bool = False
    _load_error: str | None = None

    def __new__(cls) -> "ElectricityDataLoader":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def get_data(self) -> pd.DataFrame:
        """Return the full cached DataFrame. Loads from HuggingFace on first call."""
        if self._data is not None:
            return self._data
        self._load()
        return self._data

    def get_region(self, region: str) -> pd.DataFrame:
        """Return data for a single region, sorted by time."""
        df = self.get_data()
        return df[df["region"] == region].sort_values("timestamp").reset_index(drop=True)

    def get_latest(self, region: str | None = None, hours: int = 24) -> list[dict]:
        """Return the most recent N hours as a list of dicts.

        Args:
            region: Filter to specific region (None = all regions).
            hours: Number of hours to return.
        """
        df = self.get_data()
        if region:
            df = df[df["region"] == region]
        df = df.sort_values("timestamp").tail(hours * 4)  # 4 regions per hour
        # Take the last `hours` unique timestamps for each region
        if region:
            df = df.tail(hours)
        else:
            # Get last N unique timestamps across all regions
            latest_ts = df["timestamp"].unique()[-hours:]
            df = df[df["timestamp"].isin(latest_ts)]
        return df.to_dict(orient="records")

    def get_summary(self) -> dict:
        """Return a KPI snapshot of current electricity demand."""
        df = self.get_data()
        latest_ts = df["timestamp"].max()
        latest = df[df["timestamp"] == latest_ts]

        total = latest["demand_mw"].sum()
        peak = df.groupby("region")["demand_mw"].max()

        return {
            "timestamp": latest_ts,
            "national_total_mw": round(float(total), 1),
            "regions": {
                row["region"]: {
                    "name": REGION_NAMES.get(row["region"], row["region"]),
                    "current_mw": round(float(row["demand_mw"]), 1),
                    "color": REGION_COLORS.get(row["region"], "#94a3b8"),
                    "peak_mw": round(float(peak.get(row["region"], 0)), 1),
                }
                for _, row in latest.iterrows()
            },
            "avg_national_mw": round(float(df["demand_mw"].mean()), 1),
            "peak_national_mw": round(float(df["demand_mw"].max()), 1),
            "data_points": len(df),
            "time_range": {
                "start": str(df["timestamp"].min()),
                "end": str(df["timestamp"].max()),
            },
        }

    def predict(
        self, region: str, hours: int = 24, confidence: float = 0.9
    ) -> list[dict]:
        """Simple statistical forecast using linear trend + seasonal means.

        Args:
            region: Region code (N, NE, S, SE).
            hours: Forecast horizon in hours.
            confidence: Confidence level for bounds (0.8, 0.9, 0.95).
        """
        df = self.get_region(region)
        if df.empty:
            return []

        # Use last 720 hours (30 days) for trend estimation
        recent = df.tail(720).copy()
        recent["hour_idx"] = range(len(recent))

        # Linear regression for trend
        x = recent["hour_idx"].values.astype(float)
        y = recent["demand_mw"].values.astype(float)
        if len(x) < 2:
            return []

        slope = np.polyfit(x, y, 1)[0]

        # Hourly seasonal pattern from last 7 days
        recent["hour_of_day"] = recent["timestamp"].dt.hour
        seasonal = recent.groupby("hour_of_day")["demand_mw"].mean()
        overall_mean = seasonal.mean()

        # Residual std for confidence bands
        residuals = y - np.polyval(np.polyfit(x, y, 1), x)
        resid_std = float(np.std(residuals))
        z_factor = {0.8: 1.28, 0.9: 1.645, 0.95: 1.96}.get(confidence, 1.645)

        last_ts = df["timestamp"].max()
        predictions = []
        for h in range(1, hours + 1):
            ts = last_ts + pd.Timedelta(hours=h)
            hour_of_day = ts.hour
            trend_val = y[-1] + slope * h
            seasonal_adj = seasonal.get(hour_of_day, overall_mean) - overall_mean
            predicted = trend_val + seasonal_adj

            predictions.append({
                "timestamp": ts.isoformat(),
                "hour": hour_of_day,
                "predicted_mw": round(float(predicted), 1),
                "lower_bound": round(float(predicted - z_factor * resid_std), 1),
                "upper_bound": round(float(predicted + z_factor * resid_std), 1),
                "region": region,
            })

        return predictions

    def _load(self) -> None:
        """Load the dataset from HuggingFace (called once, cached)."""
        with self._lock:
            if self._loaded:
                return
            try:
                log.info("Loading electricity dataset from HuggingFace: %s", DATASET_ID)
                from datasets import load_dataset

                ds = load_dataset(DATASET_ID, split="train")
                df = ds.to_pandas()

                # Rename and standardize columns
                df = df.rename(columns={
                    "id_subsistema": "region",
                    "din_instante": "timestamp",
                    "val_cargaenergiahomwmed": "demand_mw",
                })

                # Parse timestamps
                df["timestamp"] = pd.to_datetime(df["timestamp"])

                # Keep only needed columns
                df = df[["timestamp", "region", "demand_mw"]].dropna()
                df = df.sort_values("timestamp").reset_index(drop=True)

                self._data = df
                self._loaded = True
                log.info(
                    "Electricity dataset loaded: %d rows, %d regions, range=%s to %s",
                    len(df),
                    df["region"].nunique(),
                    df["timestamp"].min(),
                    df["timestamp"].max(),
                )
            except Exception as e:
                self._load_error = str(e)
                log.error("Failed to load electricity dataset: %s", e)
                # Create fallback synthetic data so the dashboard still works
                self._create_fallback_data()

    def _create_fallback_data(self) -> None:
        """Generate synthetic hourly electricity data if HuggingFace is unreachable."""
        log.warning("Creating fallback synthetic electricity data")
        dates = pd.date_range("2024-01-01", periods=8760, freq="h")
        rows = []
        for region in ["N", "NE", "S", "SE"]:
            base = {"N": 5000, "NE": 10000, "S": 11000, "SE": 35000}[region]
            for i, ts in enumerate(dates):
                hour = ts.hour
                day_of_year = ts.timetuple().tm_yday
                # Hourly pattern (peak at 2pm)
                hourly = 1 + 0.15 * np.sin(np.pi * (hour - 6) / 12)
                # Weekly pattern (lower on weekends)
                weekly = 1 - 0.08 * (ts.weekday() >= 5)
                # Annual pattern (higher in summer for SE/S)
                annual = 1 + 0.1 * np.cos(2 * np.pi * (day_of_year - 200) / 365)
                noise = np.random.normal(1, 0.03)
                val = base * hourly * weekly * annual * noise
                rows.append({
                    "timestamp": ts,
                    "region": region,
                    "demand_mw": round(val, 1),
                })
        self._data = pd.DataFrame(rows)
        self._loaded = True
        log.info("Fallback data created: %d rows", len(self._data))


def get_electricity_loader() -> ElectricityDataLoader:
    """Get the singleton electricity data loader."""
    return ElectricityDataLoader()

"""Data loading utilities for training and inference pipelines."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class DataLoader:
    """Loads and validates demand data from various sources.

    Supports CSV, Parquet, and database sources.
    """

    @staticmethod
    def from_csv(path: str | Path, date_col: str = "date") -> pd.DataFrame:
        """Load demand data from a CSV file.

        Expected columns: date, product_id, quantity_sold, [revenue, is_promotion, ...]
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")

        df = pd.read_csv(path)
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values([date_col]).reset_index(drop=True)
        log.info("Loaded %d rows from %s", len(df), path)
        return df

    @staticmethod
    def from_parquet(path: str | Path) -> pd.DataFrame:
        """Load demand data from a Parquet file."""
        path = Path(path)
        df = pd.read_parquet(path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True) if "date" in df.columns else df
        log.info("Loaded %d rows from %s", len(df), path)
        return df

    @staticmethod
    def generate_synthetic_data(
        n_days: int = 730,
        n_products: int = 1,
        base_demand: float = 200.0,
        trend: float = 0.02,
        noise_std: float = 0.15,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Generate synthetic demand data for testing and demos.

        Creates realistic demand patterns with trend, weekly seasonality, and noise.

        Args:
            n_days: Number of days of historical data.
            n_products: Number of unique products.
            base_demand: Average daily demand.
            trend: Linear trend coefficient (e.g., 0.02 = 2% growth per day).
            noise_std: Standard deviation of multiplicative noise.
            seed: Random seed for reproducibility.

        Returns:
            DataFrame with columns: date, product_id, quantity_sold, revenue, is_promotion.
        """
        rng = np.random.default_rng(seed)
        dates = pd.date_range(end=pd.Timestamp.now().date(), periods=n_days, freq="D")

        rows = []
        for pid in range(1, n_products + 1):
            product_base = base_demand * (0.5 + rng.random())
            for i, d in enumerate(dates):
                # Trend + weekly seasonality + noise
                demand = (
                    product_base
                    * (1 + trend * i)
                    * (1 + 0.3 * np.sin(2 * np.pi * i / 7))  # day-of-week
                    * (1 + 0.15 * np.sin(2 * np.pi * i / 365))  # yearly
                    * rng.lognormal(0, noise_std)
                )
                rows.append({
                    "date": d,
                    "product_id": pid,
                    "quantity_sold": round(demand, 1),
                    "revenue": round(demand * (10 + 5 * rng.random()), 2),
                    "is_promotion": rng.random() < 0.1,
                })

        df = pd.DataFrame(rows)
        log.info("Generated synthetic data: %d rows, %d products", len(df), n_products)
        return df

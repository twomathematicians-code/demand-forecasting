"""Test fixtures for demand forecasting."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_demand_df() -> pd.DataFrame:
    """Generate a small synthetic demand dataset for testing."""
    rng = np.random.default_rng(42)
    dates = pd.date_range(start="2022-01-01", periods=1000, freq="D")
    data = []
    for i, d in enumerate(dates):
        demand = 200 * (1 + 0.001 * i) * (1 + 0.3 * np.sin(2 * np.pi * i / 7)) * rng.lognormal(0, 0.1)
        data.append({
            "date": d,
            "product_id": 1,
            "quantity_sold": round(demand, 1),
            "revenue": round(demand * 12.5, 2),
            "is_promotion": rng.random() < 0.1,
        })
    return pd.DataFrame(data)


@pytest.fixture
def sample_time_series() -> np.ndarray:
    """Simple time series for SARIMA testing."""
    rng = np.random.default_rng(42)
    t = np.arange(200)
    return 100 + 0.5 * t + 20 * np.sin(2 * np.pi * t / 7) + rng.normal(0, 5, 200)


@pytest.fixture
def feature_df(sample_demand_df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame with pre-built features for LightGBM testing."""
    from src.features.features import FeatureEngineer
    engineer = FeatureEngineer()
    X, y = engineer.fit_transform(sample_demand_df)
    return X, y

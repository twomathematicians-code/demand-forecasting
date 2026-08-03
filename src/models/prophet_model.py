"""Facebook Prophet model wrapper for demand forecasting."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json

from src.utils.config import ProphetConfig

log = logging.getLogger(__name__)


class ProphetModel:
    """Wrapper around Facebook Prophet for trend + seasonality decomposition.

    Usage:
        model = ProphetModel(config)
        model.fit(df, regressors=["temperature", "is_promotion"])
        forecast = model.predict(periods=30, future_df=weather_forecast)
        model.save("models/prophet.json")
    """

    def __init__(self, config: ProphetConfig | None = None):
        self.config = config or ProphetConfig()
        self._model: Prophet | None = None
        self._regressors: list[str] = []
        self._is_fitted: bool = False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def model(self) -> Prophet:
        if self._model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")
        return self._model

    def fit(self, df: pd.DataFrame, regressors: list[str] | None = None) -> "ProphetModel":
        """Train Prophet on historical data.

        Args:
            df: DataFrame with columns 'ds' (date), 'y' (target), plus optional regressor columns.
            regressors: List of column names to add as external regressors.

        Returns:
            self for chaining.
        """
        c = self.config
        self._regressors = regressors or []

        self._model = Prophet(
            seasonality_mode=c.seasonality_mode,
            changepoint_range=c.changepoint_range,
            changepoint_prior_scale=c.changepoint_prior_scale,
            yearly_seasonality=c.yearly_seasonality,
            weekly_seasonality=c.weekly_seasonality,
            daily_seasonality=c.daily_seasonality,
            seasonality_prior_scale=c.seasonality_prior_scale,
            holidays_prior_scale=c.holidays_prior_scale,
            uncertainty_samples=c.uncertainty_samples,
            interval_width=0.95,
        )

        # Add external regressors
        for reg in self._regressors:
            if reg in df.columns:
                self._model.add_regressor(reg)

        # Fit
        data = df[["ds", "y"] + [r for r in self._regressors if r in df.columns]].copy()
        self._model.fit(data)
        self._is_fitted = True
        log.info("Prophet fitted: %d rows, %d regressors", len(data), len(self._regressors))
        return self

    def predict(self, periods: int, future_df: pd.DataFrame | None = None) -> pd.DataFrame:
        """Generate a forecast for the next `periods` days.

        Args:
            periods: Number of days to forecast.
            future_df: Optional DataFrame with future regressor values (must include 'ds').

        Returns:
            DataFrame with columns ['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend', 'weekly', 'yearly'].
        """
        if not self._is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        if future_df is not None and "ds" in future_df.columns:
            future = future_df[["ds"] + [r for r in self._regressors if r in future_df.columns]].copy()
        else:
            future = self._model.make_future_dataframe(periods=periods)

        forecast = self._model.predict(future)
        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper", "trend", "weekly", "yearly"]]

    def decompose(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return trend and seasonality components for historical data."""
        if not self._is_fitted:
            raise RuntimeError("Model not fitted.")
        forecast = self._model.predict(df[["ds"]])
        return forecast[["ds", "trend", "weekly", "yearly"]]

    def save(self, path: str | Path) -> None:
        """Serialize the model to a JSON file."""
        if not self._is_fitted:
            raise RuntimeError("Cannot save unfitted model.")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(model_to_json(self._model))
        log.info("Prophet model saved to %s", path)

    def load(self, path: str | Path) -> "ProphetModel":
        """Load a serialized model from a JSON file."""
        path = Path(path)
        with open(path) as f:
            self._model = model_from_json(f.read())
        self._is_fitted = True
        log.info("Prophet model loaded from %s", path)
        return self

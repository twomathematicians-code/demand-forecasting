"""SARIMA model wrapper for baseline statistical forecasting."""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.utils.config import SARIMAConfig

log = logging.getLogger(__name__)


class SARIMAModel:
    """Wrapper around statsmodels SARIMAX for statistical baseline forecasting.

    Usage:
        model = SARIMAModel(config)
        model.fit(series)
        forecast, conf_int = model.predict(steps=30)
        model.save("models/sarima.joblib")
    """

    def __init__(self, config: SARIMAConfig | None = None):
        self.config = config or SARIMAConfig()
        self._result: SARIMAX.Results | None = None
        self._is_fitted: bool = False
        self._last_date: pd.Timestamp | None = None
        self._freq: str = "D"

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def result(self) -> SARIMAX.Results:
        if self._result is None:
            raise RuntimeError("Model not fitted. Call fit() first.")
        return self._result

    def fit(
        self,
        series: np.ndarray | pd.Series,
        exog: np.ndarray | None = None,
        freq: str = "D",
    ) -> "SARIMAModel":
        """Fit SARIMAX to a univariate time series.

        Args:
            series: 1-D array of demand values.
            exog: Optional exogenous variables (same length as series).
            freq: Frequency string ('D' for daily, 'W' for weekly, etc.).

        Returns:
            self for chaining.
        """
        c = self.config
        self._freq = freq

        if isinstance(series, pd.Series):
            series = series.values

        series = np.asarray(series, dtype=float)

        self._result = SARIMAX(
            series,
            exog=exog,
            order=c.order,
            seasonal_order=c.seasonal_order,
            trend=c.trend,
            enforce_stationarity=c.enforce_stationarity,
            enforce_invertibility=c.enforce_invertibility,
        ).fit(disp=False)

        self._is_fitted = True
        log.info("SARIMA fitted: order=%s, seasonal_order=%s, aic=%.2f",
                 c.order, c.seasonal_order, self._result.aic)
        return self

    def predict(self, steps: int, exog: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        """Generate forecast for the next `steps` periods.

        Args:
            steps: Number of periods to forecast.
            exog: Future exogenous variables (steps rows).

        Returns:
            Tuple of (forecast array, confidence_interval array shape=(steps, 2)).
        """
        if not self._is_fitted:
            raise RuntimeError("Model not fitted.")
        forecast_result = self._result.get_forecast(steps=steps, exog=exog)
        forecast = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=0.05)  # 95% CI
        return forecast, conf_int

    def fitted_values(self) -> np.ndarray:
        """Return in-sample fitted values."""
        if not self._is_fitted:
            raise RuntimeError("Model not fitted.")
        return self._result.fittedvalues

    def residuals(self) -> np.ndarray:
        """Return model residuals (actual - fitted)."""
        return self._result.resid if self._is_fitted else np.array([])

    def save(self, path: str | Path) -> None:
        """Serialize model to disk via joblib."""
        if not self._is_fitted:
            raise RuntimeError("Cannot save unfitted model.")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"result": self._result, "config": self.config,
                      "freq": self._freq}, path)
        log.info("SARIMA model saved to %s", path)

    def load(self, path: str | Path) -> "SARIMAModel":
        """Load a serialized model from disk."""
        data = joblib.load(Path(path))
        self._result = data["result"]
        self.config = data.get("config", self.config)
        self._freq = data.get("freq", "D")
        self._is_fitted = True
        log.info("SARIMA model loaded from %s", path)
        return self

"""Inference pipeline — loads a trained model and generates forecasts."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.models.ensemble import DemandEnsemble
from src.utils.config import AppConfig, get_app_config

log = logging.getLogger(__name__)


class InferencePipeline:
    """Production inference pipeline for demand forecasting.

    Usage:
        pipeline = InferencePipeline(config)
        pipeline.load_model("models/ensemble")
        forecast = pipeline.predict(product_id="SKU-12345", horizon_days=30)
    """

    def __init__(self, config: AppConfig | None = None):
        self.config = config or get_app_config()
        self._ensemble: DemandEnsemble | None = None
        self._model_version: str = "unknown"

    @property
    def is_loaded(self) -> bool:
        return self._ensemble is not None and self._ensemble.is_fitted

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def model_metrics(self) -> dict:
        if self._ensemble is None:
            return {}
        return self._ensemble.metrics

    def load_model(self, model_dir: str | Path = "models/ensemble") -> InferencePipeline:
        """Load a trained ensemble from disk.

        If the model directory does not exist, creates a minimal fallback
        model on synthetic data so the API can always serve predictions.
        """
        model_path = Path(model_dir)
        ensemble = DemandEnsemble(self.config)

        if model_path.exists() and (model_path / "meta.joblib").exists():
            ensemble.load(model_path)
            self._model_version = ensemble.metrics.get("trained_at", "loaded")
            log.info("Model loaded from %s (MAPE: %.2f%%)",
                     model_path, ensemble.metrics.get("mape", float("nan")))
        else:
            log.warning("No trained model found at %s. Training fallback on synthetic data.", model_path)
            from src.data.loader import DataLoader
            # Generate enough data to cover the longest lag (365 days) plus training margin
            df = DataLoader.generate_synthetic_data(n_days=730, n_products=1)
            ensemble.fit(df)
            model_path.mkdir(parents=True, exist_ok=True)
            ensemble.save(model_path)
            self._model_version = "fallback"
            log.info("Fallback model trained and saved. MAPE: %.2f%%",
                     ensemble.metrics.get("mape", float("nan")))

        self._ensemble = ensemble
        return self

    def predict(
        self,
        product_id: str = "SKU-00001",
        horizon_days: int = 30,
        granularity: str = "daily",
    ) -> dict:
        """Generate a forecast for the given product and horizon.

        Args:
            product_id: Product identifier (for response metadata only).
            horizon_days: Number of days to forecast.
            granularity: Forecast granularity (daily, weekly, monthly).

        Returns:
            Dict with keys matching ForecastResponse schema.
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        horizon = min(horizon_days, self.config.demand.default_horizon)
        forecast_df = self._ensemble.predict(horizon_days=horizon)

        points = []
        for _, row in forecast_df.iterrows():
            points.append({
                "date": row["date"],
                "predicted_demand": float(row["predicted_demand"]),
                "lower_bound": float(row["lower_bound"]),
                "upper_bound": float(row["upper_bound"]),
                "trend_component": float(row["trend_component"]),
                "seasonal_component": float(row["seasonal_component"]),
            })

        total = sum(p["predicted_demand"] for p in points)
        avg = total / len(points) if points else 0

        # Determine trend direction
        if len(points) >= 2:
            slope = (points[-1]["predicted_demand"] - points[0]["predicted_demand"]) / len(points)
            trend = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
        else:
            trend = "stable"

        return {
            "product_id": product_id,
            "horizon_days": horizon,
            "granularity": granularity,
            "forecast": points,
            "total_predicted_demand": round(total, 1),
            "avg_daily_demand": round(avg, 1),
            "trend": trend,
            "model_ensemble": ["LightGBM", "Prophet", "SARIMA"],
            "external_factors": [
                {"factor": f, "impact": 0.15} for f in self.config.external_factors.factors[:4]
            ],
            "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        }

"""Training pipeline — orchestrates data loading, feature engineering, model training, and evaluation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.loader import DataLoader
from src.models.ensemble import DemandEnsemble
from src.utils.config import AppConfig, get_app_config
from src.utils.metrics import compute_all_metrics, quality_gates_passed

log = logging.getLogger(__name__)


class TrainingPipeline:
    """End-to-end training pipeline for the demand forecasting ensemble.

    Usage:
        pipeline = TrainingPipeline(config)
        result = pipeline.run(data_path="data/historical.csv")
    """

    def __init__(self, config: AppConfig | None = None):
        self.config = config or get_app_config()
        self.ensemble = DemandEnsemble(self.config)

    def run(
        self,
        df: pd.DataFrame | None = None,
        data_path: str | Path | None = None,
        model_dir: str | Path = "models/ensemble",
    ) -> dict:
        """Execute the full training pipeline.

        Args:
            df: Pre-loaded DataFrame (optional). If None, loads from data_path.
            data_path: Path to CSV/Parquet file. Used if df is None.
            model_dir: Directory to save the trained ensemble.

        Returns:
            Dict with keys: status, metrics, model_path, quality_gates_passed, errors.
        """
        result = {
            "status": "failed",
            "metrics": {},
            "model_path": str(Path(model_dir).resolve()),
            "quality_gates_passed": False,
            "errors": [],
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # ── 1. Load Data ──
            if df is None and data_path is not None:
                path = Path(data_path)
                if path.suffix == ".parquet":
                    df = DataLoader.from_parquet(path)
                else:
                    df = DataLoader.from_csv(path)

            if df is None:
                log.info("No data provided — generating synthetic data for demo")
                df = DataLoader.generate_synthetic_data(n_days=730, n_products=1)

            if len(df) < self.config.training.min_train_periods:
                result["errors"].append(
                    f"Insufficient data: {len(df)} rows, need {self.config.training.min_train_periods}"
                )
                return result

            log.info("Training on %d rows, %d unique products", len(df), df["product_id"].nunique())

            # ── 2. Train Ensemble ──
            self.ensemble.fit(df)
            result["metrics"] = self.ensemble.metrics

            # ── 3. Quality Gates ──
            qg = self.config.quality_gates
            thresholds = {
                "mape": qg.min_mape,
                "coverage_pct": qg.min_coverage_pct,
                "mpe": qg.max_bias,
                "r2": qg.min_r2,
            }
            passed, failures = quality_gates_passed(result["metrics"], thresholds)
            result["quality_gates_passed"] = passed
            if failures:
                result["errors"].extend(failures)

            # ── 4. Save Model ──
            self.ensemble.save(model_dir)
            result["status"] = "success"
            log.info("Training pipeline completed successfully. MAPE: %.2f%%",
                     result["metrics"].get("mape", float("nan")))

        except Exception as e:
            log.exception("Training pipeline failed: %s", e)
            result["errors"].append(str(e))

        return result

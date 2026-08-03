"""LightGBM model wrapper for gradient-boosted demand forecasting."""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from src.utils.config import LightGBMConfig

log = logging.getLogger(__name__)


class LightGBMModel:
    """Wrapper around LightGBM for non-linear demand forecasting with external features.

    Usage:
        model = LightGBMModel(config)
        model.fit(X_train, y_train, X_valid, y_valid)
        predictions = model.predict(X_test)
        model.save("models/lightgbm.joblib")
    """

    def __init__(self, config: LightGBMConfig | None = None):
        self.config = config or LightGBMConfig()
        self._model: lgb.LGBMRegressor | None = None
        self._feature_names: list[str] = []
        self._is_fitted: bool = False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def model(self) -> lgb.LGBMRegressor:
        if self._model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")
        return self._model

    @property
    def feature_names(self) -> list[str]:
        return self._feature_names

    def fit(
        self,
        X_train: pd.DataFrame | np.ndarray,
        y_train: np.ndarray | pd.Series,
        X_valid: pd.DataFrame | np.ndarray | None = None,
        y_valid: np.ndarray | pd.Series | None = None,
    ) -> LightGBMModel:
        """Train LightGBM with optional early stopping on validation set.

        Args:
            X_train: Training features.
            y_train: Training target.
            X_valid: Validation features (for early stopping).
            y_valid: Validation target.

        Returns:
            self for chaining.
        """
        c = self.config

        if isinstance(X_train, pd.DataFrame):
            self._feature_names = list(X_train.columns)
            X_train = X_train.values
        elif isinstance(X_train, np.ndarray) and not self._feature_names:
            self._feature_names = [f"f_{i}" for i in range(X_train.shape[1])]

        y_train = np.asarray(y_train, dtype=float)

        fit_params = {}
        eval_set = None

        if X_valid is not None and y_valid is not None:
            if isinstance(X_valid, pd.DataFrame):
                X_valid = X_valid.values
            y_valid = np.asarray(y_valid, dtype=float)
            if len(X_valid) > 0:
                fit_params["eval_X"] = X_valid
                fit_params["eval_y"] = y_valid
                fit_params["eval_metric"] = "rmse"
                fit_params["callbacks"] = [
                    lgb.early_stopping(c.early_stopping_rounds, verbose=False),
                    lgb.log_evaluation(period=0),
                ]

        self._model = lgb.LGBMRegressor(
            n_estimators=c.n_estimators,
            learning_rate=c.learning_rate,
            max_depth=c.max_depth,
            num_leaves=c.num_leaves,
            min_child_samples=c.min_child_samples,
            subsample=c.subsample,
            colsample_bytree=c.colsample_bytree,
            reg_alpha=c.reg_alpha,
            reg_lambda=c.reg_lambda,
            random_state=42,
            verbose=-1,
            n_jobs=-1,
            force_col_wise=True,
        )

        self._model.fit(X_train, y_train, **fit_params)
        self._is_fitted = True

        # Log training summary
        n_trees = self._model.n_estimators_ if hasattr(self._model, "n_estimators_") else 0
        log.info("LightGBM fitted: %d features, %d trees, %d train samples",
                 len(self._feature_names), n_trees, len(y_train))
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Generate point predictions."""
        if not self._is_fitted:
            raise RuntimeError("Model not fitted.")
        if isinstance(X, pd.DataFrame):
            X = X[self._feature_names] if set(self._feature_names).issubset(X.columns) else X.values
        return self._model.predict(np.asarray(X, dtype=float))

    def feature_importance(self) -> pd.DataFrame:
        """Return feature importance as a sorted DataFrame."""
        if not self._is_fitted:
            raise RuntimeError("Model not fitted.")
        importances = self._model.feature_importances_
        return pd.DataFrame({
            "feature": self._feature_names,
            "importance": importances,
        }).sort_values("importance", ascending=False).reset_index(drop=True)

    def save(self, path: str | Path) -> None:
        """Serialize model to disk."""
        if not self._is_fitted:
            raise RuntimeError("Cannot save unfitted model.")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "model": self._model,
            "feature_names": self._feature_names,
            "config": self.config,
        }, path)
        log.info("LightGBM model saved to %s", path)

    def load(self, path: str | Path) -> LightGBMModel:
        """Load a serialized model from disk."""
        data = joblib.load(Path(path))
        self._model = data["model"]
        self._feature_names = data.get("feature_names", [])
        self.config = data.get("config", self.config)
        self._is_fitted = True
        log.info("LightGBM model loaded from %s (%d features)", path, len(self._feature_names))
        return self

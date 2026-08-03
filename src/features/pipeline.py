"""Feature pipeline wrapper for consistent train/inference transforms."""

from __future__ import annotations

import pandas as pd

from src.features.features import FeatureEngineer
from src.utils.config import FeatureConfig


class FeaturePipeline:
    """Wraps FeatureEngineer with fit/transform semantics matching sklearn Pipeline.

    Usage:
        pipeline = FeaturePipeline(config)
        X_train, y_train = pipeline.fit_transform(train_df)
        X_pred = pipeline.transform(new_df)
    """

    def __init__(self, config: FeatureConfig | None = None):
        self.config = config or FeatureConfig()
        self._engineer = FeatureEngineer(self.config)
        self._fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    @property
    def feature_names(self) -> list[str]:
        return self._engineer.feature_names

    def fit_transform(self, df: pd.DataFrame, target_col: str = "quantity_sold") -> tuple[pd.DataFrame, pd.Series]:
        self._fitted = True
        return self._engineer.fit_transform(df, target_col)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted:
            raise RuntimeError("FeaturePipeline must be fit before transform. Call fit_transform() first.")
        return self._engineer.transform(df)

    def fit(self, df: pd.DataFrame, target_col: str = "quantity_sold") -> FeaturePipeline:
        """Fit without returning data (useful for Pipeline integration)."""
        self.fit_transform(df, target_col)
        return self

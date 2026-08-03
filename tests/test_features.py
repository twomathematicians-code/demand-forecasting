"""Tests for feature engineering."""

import pandas as pd
from src.features.features import FeatureEngineer
from src.utils.config import FeatureConfig


class TestFeatureEngineer:
    def test_fit_transform(self, sample_demand_df):
        engineer = FeatureEngineer()
        X, y = engineer.fit_transform(sample_demand_df)
        assert len(X) > 0
        assert len(y) > 0
        assert len(X) == len(y)
        assert "lag_1" in X.columns or len(X.columns) > 5

    def test_transform_after_fit(self, sample_demand_df):
        engineer = FeatureEngineer()
        X_train, y_train = engineer.fit_transform(sample_demand_df)
        X_new = engineer.transform(sample_demand_df.tail(60))
        assert X_new.shape[1] == X_train.shape[1]

    def test_calendar_features(self, sample_demand_df):
        engineer = FeatureEngineer()
        X, _ = engineer.fit_transform(sample_demand_df)
        assert "day_of_week" in X.columns
        assert "month" in X.columns
        assert "is_weekend" in X.columns

    def test_cyclical_encoding(self, sample_demand_df):
        config = FeatureConfig(cyclical_encoding=True)
        engineer = FeatureEngineer(config)
        X, _ = engineer.fit_transform(sample_demand_df)
        assert "dow_sin" in X.columns
        assert "dow_cos" in X.columns
        assert "month_sin" in X.columns

    def test_no_nan_in_output(self, sample_demand_df):
        engineer = FeatureEngineer()
        X, y = engineer.fit_transform(sample_demand_df)
        assert not X.isna().any().any()
        assert not y.isna().any()

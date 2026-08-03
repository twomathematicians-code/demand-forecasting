"""Tests for model wrappers."""

import numpy as np
import pandas as pd

from src.models.ensemble import DemandEnsemble
from src.models.lightgbm_model import LightGBMModel
from src.models.prophet_model import ProphetModel
from src.models.sarima_model import SARIMAModel
from src.utils.config import AppConfig


class TestProphetModel:
    def test_fit_predict(self, sample_demand_df):
        df = sample_demand_df.rename(columns={"date": "ds", "quantity_sold": "y"})
        model = ProphetModel()
        model.fit(df)
        assert model.is_fitted
        forecast = model.predict(periods=14)
        assert len(forecast) >= 14
        assert "yhat" in forecast.columns
        assert "yhat_lower" in forecast.columns
        assert "yhat_upper" in forecast.columns

    def test_save_load(self, sample_demand_df, tmp_path):
        df = sample_demand_df.rename(columns={"date": "ds", "quantity_sold": "y"})
        model = ProphetModel()
        model.fit(df)
        path = tmp_path / "prophet.json"
        model.save(path)
        model2 = ProphetModel()
        model2.load(path)
        assert model2.is_fitted
        forecast = model2.predict(periods=7)
        # Prophet returns historical + future rows; future rows should be >= requested periods
        assert len(forecast) >= 7


class TestSARIMAModel:
    def test_fit_predict(self, sample_time_series):
        model = SARIMAModel()
        model.fit(sample_time_series)
        assert model.is_fitted
        forecast, conf_int = model.predict(steps=30)
        assert len(forecast) == 30
        assert conf_int.shape == (30, 2)

    def test_save_load(self, sample_time_series, tmp_path):
        model = SARIMAModel()
        model.fit(sample_time_series)
        path = tmp_path / "sarima.joblib"
        model.save(path)
        model2 = SARIMAModel()
        model2.load(path)
        assert model2.is_fitted
        forecast, _ = model2.predict(steps=10)
        assert len(forecast) == 10

    def test_fitted_values(self, sample_time_series):
        model = SARIMAModel()
        model.fit(sample_time_series)
        fitted = model.fitted_values()
        assert len(fitted) == len(sample_time_series)


class TestLightGBMModel:
    def test_fit_predict(self, feature_df):
        X, y = feature_df
        n_train = int(len(X) * 0.8)
        X_train, y_train = X.iloc[:n_train], y.iloc[:n_train]
        X_test, y_test = X.iloc[n_train:], y.iloc[n_train:]

        model = LightGBMModel()
        model.fit(X_train, y_train, X_test, y_test)
        assert model.is_fitted

        preds = model.predict(X_test)
        assert len(preds) == len(X_test)
        assert not np.any(np.isnan(preds))

    def test_feature_importance(self, feature_df):
        X, y = feature_df
        model = LightGBMModel()
        model.fit(X.iloc[:300], y.iloc[:300])
        importance = model.feature_importance()
        assert len(importance) > 0
        assert "feature" in importance.columns
        assert "importance" in importance.columns

    def test_save_load(self, feature_df, tmp_path):
        X, y = feature_df
        model = LightGBMModel()
        model.fit(X.iloc[:300], y.iloc[:300])
        path = tmp_path / "lgb.joblib"
        model.save(path)

        model2 = LightGBMModel()
        model2.load(path)
        assert model2.is_fitted
        preds = model2.predict(X.iloc[:10])
        assert len(preds) == 10


class TestDemandEnsemble:
    def test_fit_predict(self, sample_demand_df):
        config = AppConfig.default()
        ensemble = DemandEnsemble(config)
        ensemble.fit(sample_demand_df)
        assert ensemble.is_fitted

        forecast = ensemble.predict(horizon_days=14)
        assert isinstance(forecast, pd.DataFrame)
        assert "predicted_demand" in forecast.columns
        assert len(forecast) == 14

    def test_metrics_after_fit(self, sample_demand_df):
        config = AppConfig.default()
        ensemble = DemandEnsemble(config)
        ensemble.fit(sample_demand_df)
        metrics = ensemble.metrics
        assert "mape" in metrics
        assert "rmse" in metrics

    def test_save_load(self, sample_demand_df, tmp_path):
        config = AppConfig.default()
        ensemble = DemandEnsemble(config)
        ensemble.fit(sample_demand_df)

        path = tmp_path / "ensemble"
        ensemble.save(path)

        ensemble2 = DemandEnsemble(config)
        ensemble2.load(path)
        assert ensemble2.is_fitted
        forecast = ensemble2.predict(horizon_days=7)
        assert len(forecast) == 7

"""Tests for configuration system."""

import pytest
from src.utils.config import (
    AppConfig, Settings,
    LightGBMConfig, ProphetConfig, SARIMAConfig,
    QualityGatesConfig, FeatureConfig,
)


class TestAppConfig:
    def test_default_config(self):
        config = AppConfig.default()
        assert config.demand.default_horizon == 30
        assert config.models.lightgbm.n_estimators == 500
        assert config.models.prophet.seasonality_mode == "multiplicative"
        assert config.models.sarima.order == (2, 1, 2)
        assert config.quality_gates.min_mape == 15.0
        assert "weather" in config.external_factors.factors

    def test_from_yaml(self):
        import os
        # Find the config file relative to project root
        yaml_path = os.path.join(
            os.path.dirname(__file__), "..", "configs", "model_config.yaml"
        )
        if os.path.exists(yaml_path):
            config = AppConfig.from_yaml(yaml_path)
            assert config.demand.default_horizon > 0


class TestSettings:
    def test_default_settings(self):
        settings = Settings()
        assert settings.environment == "development"
        assert settings.db_host == "localhost"
        assert settings.db_port == 5432

    def test_database_url(self):
        settings = Settings()
        url = settings.database_url
        assert "postgresql+asyncpg" in url
        assert settings.db_user in url
        assert str(settings.db_port) in url

    def test_sync_database_url(self):
        settings = Settings()
        url = settings.sync_database_url
        assert "postgresql://" in url


class TestModelConfigValidation:
    def test_lightgbm_bounds(self):
        with pytest.raises(Exception):
            LightGBMConfig(n_estimators=0)  # below minimum

    def test_sarima_order_validation(self):
        with pytest.raises(Exception):
            SARIMAConfig(order=(1, 2))  # not enough elements

    def test_prophet_mode_validation(self):
        config = ProphetConfig(seasonality_mode="additive")
        assert config.seasonality_mode == "additive"


class TestQualityGates:
    def test_thresholds(self):
        gates = QualityGatesConfig()
        assert gates.min_mape == 15.0
        assert 0.0 < gates.min_coverage_pct <= 1.0
        assert gates.max_bias >= 0
        assert 0.0 <= gates.min_r2 <= 1.0

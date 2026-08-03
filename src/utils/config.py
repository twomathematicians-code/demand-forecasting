"""Configuration system for demand forecasting.

Three-layer architecture:
  YAML files (data) -> Pydantic models (schema) -> Loader (wiring)

Usage:
    from src.utils.config import AppConfig, Settings
    app_config = AppConfig.from_yaml("configs/model_config.yaml")
    settings = Settings()
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ═══════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════

class ModelType(str, Enum):
    lightgbm = "lightgbm"
    prophet = "prophet"
    sarima = "sarima"
    ensemble = "ensemble"
    cnn_lstm = "cnn_lstm"


class Granularity(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class ModelStatus(str, Enum):
    active = "active"
    retired = "retired"
    shadow = "shadow"
    staging = "staging"


# ═══════════════════════════════════════════════════════════════════
# Per-Model Configuration
# ═══════════════════════════════════════════════════════════════════

class LightGBMConfig(BaseModel):
    """LightGBM gradient boosting configuration."""
    model_config = ConfigDict(extra="forbid")

    n_estimators: int = Field(500, ge=100, le=10000, description="Number of boosting rounds")
    learning_rate: float = Field(0.05, ge=0.001, le=1.0, description="Step size shrinkage")
    max_depth: int = Field(8, ge=2, le=31, description="Maximum tree depth")
    num_leaves: int = Field(31, ge=2, le=256, description="Maximum leaves per tree")
    min_child_samples: int = Field(20, ge=1, le=1000, description="Min data in leaf")
    subsample: float = Field(0.8, ge=0.1, le=1.0, description="Row sampling ratio")
    colsample_bytree: float = Field(0.8, ge=0.1, le=1.0, description="Column sampling ratio")
    reg_alpha: float = Field(0.0, ge=0.0, le=10.0, description="L1 regularization")
    reg_lambda: float = Field(0.0, ge=0.0, le=10.0, description="L2 regularization")
    early_stopping_rounds: int = Field(50, ge=10, le=500, description="Early stopping patience")


class ProphetConfig(BaseModel):
    """Facebook Prophet configuration."""
    model_config = ConfigDict(extra="forbid")

    seasonality_mode: Literal["additive", "multiplicative"] = "multiplicative"
    changepoint_range: float = Field(0.8, ge=0.0, le=1.0, description="Proportion of history for changepoints")
    changepoint_prior_scale: float = Field(0.05, ge=0.001, le=0.5, description="Changepoint flexibility")
    yearly_seasonality: bool = True
    weekly_seasonality: bool = True
    daily_seasonality: bool = False
    seasonality_prior_scale: float = Field(10.0, ge=0.01, le=100.0, description="Seasonality flexibility")
    holidays_prior_scale: float = Field(10.0, ge=0.01, le=100.0, description="Holiday effect flexibility")
    uncertainty_samples: int = Field(1000, ge=100, le=10000, description="MCMC samples for uncertainty")


class SARIMAConfig(BaseModel):
    """SARIMA statistical model configuration."""
    model_config = ConfigDict(extra="forbid")

    order: tuple[int, int, int] = (2, 1, 2)
    seasonal_order: tuple[int, int, int, int] = (1, 1, 1, 7)
    trend: str = "c"
    enforce_stationarity: bool = True
    enforce_invertibility: bool = True

    @field_validator("order")
    @classmethod
    def validate_order(cls, v: tuple) -> tuple:
        if len(v) != 3:
            raise ValueError(f"order must have exactly 3 elements: (p, d, q), got {v}")
        if any(x < 0 for x in v):
            raise ValueError(f"order elements must be non-negative, got {v}")
        return v

    @field_validator("seasonal_order")
    @classmethod
    def validate_seasonal_order(cls, v: tuple) -> tuple:
        if len(v) != 4:
            raise ValueError(f"seasonal_order must have exactly 4 elements: (P, D, Q, s), got {v}")
        if any(x < 0 for x in v[:3]):
            raise ValueError(f"seasonal_order first 3 elements must be non-negative, got {v}")
        if v[3] < 2:
            raise ValueError(f"seasonal period (s) must be >= 2, got {v[3]}")
        return v


class CNNLSTMConfig(BaseModel):
    """CNN-LSTM deep learning configuration (Phase 2)."""
    model_config = ConfigDict(extra="forbid")

    conv_filters: list[int] = [64, 128]
    conv_kernel_size: int = 3
    lstm_hidden: int = 128
    lstm_layers: int = 2
    dropout: float = Field(0.3, ge=0.0, le=0.8)
    learning_rate: float = Field(0.001, ge=1e-5, le=0.1)
    batch_size: int = Field(64, ge=8, le=512)
    epochs: int = Field(100, ge=10, le=1000)
    sequence_length: int = Field(60, ge=7, le=365, description="Lookback window in days")
    early_stopping_patience: int = Field(20, ge=5, le=100)


# ═══════════════════════════════════════════════════════════════════
# Top-Level Configuration
# ═══════════════════════════════════════════════════════════════════

class DemandConfig(BaseModel):
    """Core demand forecasting parameters."""
    model_config = ConfigDict(extra="forbid")

    default_horizon: int = Field(30, ge=1, le=365, description="Default forecast horizon in days")
    granularities: list[Granularity] = [Granularity.daily, Granularity.weekly, Granularity.monthly]
    confidence_level: float = Field(0.95, ge=0.50, le=0.99, description="Prediction interval confidence")


class ModelConfigs(BaseModel):
    """Container for all per-model configurations."""
    model_config = ConfigDict(extra="forbid")

    lightgbm: LightGBMConfig = LightGBMConfig()
    prophet: ProphetConfig = ProphetConfig()
    sarima: SARIMAConfig = SARIMAConfig()
    cnn_lstm: CNNLSTMConfig = CNNLSTMConfig()


class ExternalFactorsConfig(BaseModel):
    """External factors used as model regressors."""
    model_config = ConfigDict(extra="forbid")

    factors: list[str] = Field(
        default=["weather", "promotions", "holidays", "competitor_pricing"],
        description="List of external factor names to include as features",
    )
    weather_windows: list[int] = Field(
        default=[1, 7, 30],
        description="Rolling windows for weather features in days",
    )


class QualityGatesConfig(BaseModel):
    """Quality thresholds for model promotion."""
    model_config = ConfigDict(extra="forbid")

    min_mape: float = Field(15.0, description="Maximum acceptable MAPE (%) for promotion")
    min_coverage_pct: float = Field(0.85, ge=0.0, le=1.0, description="Min % of actuals inside prediction interval")
    max_bias: float = Field(5.0, description="Maximum acceptable bias (%)")
    min_r2: float = Field(0.60, ge=0.0, le=1.0, description="Minimum R-squared")
    max_rmse_ratio: float = Field(2.0, ge=0.0, description="Max RMSE / naive_RMSE ratio")


class TrainingConfig(BaseModel):
    """Training pipeline configuration."""
    model_config = ConfigDict(extra="forbid")

    train_ratio: float = Field(0.60, ge=0.4, le=0.9, description="Fraction of data for training")
    val_ratio: float = Field(0.20, ge=0.05, le=0.4, description="Fraction of data for validation")
    test_ratio: float = Field(0.20, ge=0.05, le=0.4, description="Fraction of data for testing")
    cv_folds: int = Field(5, ge=2, le=20, description="Time series cross-validation folds")
    min_train_periods: int = Field(365, ge=30, description="Minimum days of training data required")
    random_seed: int = Field(42, ge=0)


class FeatureConfig(BaseModel):
    """Feature engineering configuration."""
    model_config = ConfigDict(extra="forbid")

    lag_periods: list[int] = Field(default=[1, 2, 3, 7, 14, 30, 90, 365])
    rolling_windows: list[int] = Field(default=[7, 14, 30])
    rolling_stats: list[str] = Field(default=["mean", "std", "min", "max"])
    cyclical_encoding: bool = True
    include_date_features: bool = True
    include_cluster_features: bool = True
    max_lag_correlation: float = Field(0.95, ge=0.0, le=1.0, description="Max correlation for feature removal")


class InferenceConfig(BaseModel):
    """Inference pipeline configuration."""
    model_config = ConfigDict(extra="forbid")

    batch_max_samples: int = Field(10000, ge=100, description="Max rows per batch prediction")
    cache_ttl_seconds: int = Field(300, ge=0, description="Prediction cache TTL")
    fallback_enabled: bool = Field(True, description="Use naive forecast if model fails")
    request_timeout_seconds: int = Field(30, ge=5, le=300)


class AppConfig(BaseModel):
    """Root application configuration loaded from YAML."""
    model_config = ConfigDict(extra="forbid")

    demand: DemandConfig = DemandConfig()
    models: ModelConfigs = ModelConfigs()
    external_factors: ExternalFactorsConfig = ExternalFactorsConfig()
    quality_gates: QualityGatesConfig = QualityGatesConfig()
    training: TrainingConfig = TrainingConfig()
    features: FeatureConfig = FeatureConfig()
    inference: InferenceConfig = InferenceConfig()

    @classmethod
    def from_yaml(cls, path: str | Path) -> AppConfig:
        """Load and validate configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            Validated AppConfig instance.

        Raises:
            FileNotFoundError: If the YAML file does not exist.
            ValidationError: If the YAML content fails Pydantic validation.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        raw = yaml.safe_load(path.read_text())
        if raw is None:
            raw = {}
        return cls.model_validate(raw)

    @classmethod
    def default(cls) -> AppConfig:
        """Return an AppConfig with all defaults (no YAML needed)."""
        return cls()


# ═══════════════════════════════════════════════════════════════════
# Environment Settings (from .env / environment variables)
# ═══════════════════════════════════════════════════════════════════

class Settings(BaseSettings):
    """Runtime settings loaded from .env file and environment variables.

    All fields are prefixed with DF_ in environment variables.
    Example: DF_ENVIRONMENT=production
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DF_",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment ──
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Database ──
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "mluser"
    db_password: str = "mlpassword"
    db_name: str = "demand_forecasting"
    db_min_connections: int = Field(2, ge=1, le=50)
    db_max_connections: int = Field(10, ge=1, le=100)

    # ── MLflow ──
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "demand-forecasting"
    mlflow_artifact_root: str = "./mlflow-artifacts"

    # ── Model Artifacts ──
    model_registry_path: str = "./models"

    # ── API ──
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = Field(1, ge=1, le=8)

    # ── Kafka ──
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "demand-forecasting"
    kafka_sales_topic: str = "sales.events"
    kafka_forecast_topic: str = "forecasts.generated"
    kafka_consumer_enabled: bool = False  # Off by default — enable in production

    # ── Drift Monitoring ──
    drift_check_enabled: bool = False
    drift_check_hour: int = Field(6, ge=0, le=23)
    drift_reference_days: int = Field(90, ge=30, le=365)
    drift_current_days: int = Field(30, ge=7, le=90)

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False

    # ── Multi-Tenant ──
    tenant_id: str = "default"

    @property
    def database_url(self) -> str:
        """Build an asyncpg-compatible database URL."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def sync_database_url(self) -> str:
        """Build a sync database URL for Alembic migrations."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


# ═══════════════════════════════════════════════════════════════════
# Module-level singletons (lazy-loaded by application)
# ═══════════════════════════════════════════════════════════════════

_settings: Settings | None = None
_app_config: AppConfig | None = None


def get_settings() -> Settings:
    """Return the singleton Settings instance, loading from .env if needed."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_app_config(config_path: str | Path | None = None) -> AppConfig:
    """Return the singleton AppConfig instance, loading from YAML if needed.

    Args:
        config_path: Path to model_config.yaml. Defaults to 'configs/model_config.yaml'.
    """
    global _app_config
    if _app_config is None:
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "configs" / "model_config.yaml"
        _app_config = AppConfig.from_yaml(config_path)
    return _app_config

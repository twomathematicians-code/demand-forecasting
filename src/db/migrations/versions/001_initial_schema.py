"""Initial schema — demand forecasting core tables.

Revision ID: 001
Revises: None
Create Date: 2026-08-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all core tables for the demand forecasting system."""

    # ── actuals — Ground-truth historical demand ──
    op.execute("""
        CREATE TABLE actuals (
            actual_id      BIGSERIAL,
            product_id     INTEGER        NOT NULL,
            store_id       INTEGER        NOT NULL DEFAULT 1,
            date           DATE           NOT NULL,
            quantity_sold  NUMERIC(12,2)  NOT NULL,
            revenue        NUMERIC(14,2),
            is_promotion   BOOLEAN        DEFAULT FALSE,
            ingested_at    TIMESTAMPTZ    DEFAULT now(),

            CONSTRAINT uq_actual_product_store_date
                UNIQUE (product_id, store_id, date)
        ) PARTITION BY RANGE (date)
    """)

    # Create initial partitions for 2020-2027
    for year in range(2020, 2028):
        op.execute(f"""
            CREATE TABLE actuals_{year} PARTITION OF actuals
            FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
        """)

    # BRIN index on date (efficient for append-only workloads)
    op.execute("""
        CREATE INDEX idx_actuals_date_brin ON actuals USING BRIN (date)
        WITH (pages_per_range = 32)
    """)
    op.create_index("idx_actuals_product_date", "actuals", ["product_id", "date"])

    # ── forecasts — Model predictions ──
    op.execute("""
        CREATE TABLE forecasts (
            forecast_id      BIGSERIAL,
            model_id         INTEGER        NOT NULL,
            product_id       INTEGER        NOT NULL,
            store_id         INTEGER        NOT NULL DEFAULT 1,
            forecast_date    DATE           NOT NULL,
            target_date      DATE           NOT NULL,
            horizon_days     SMALLINT       NOT NULL,
            predicted_qty    NUMERIC(12,2)  NOT NULL,
            yhat_lower       NUMERIC(12,2),
            yhat_upper       NUMERIC(12,2),
            forecast_version VARCHAR(32),
            created_at       TIMESTAMPTZ    DEFAULT now(),

            CONSTRAINT uq_forecast_unique
                UNIQUE (model_id, product_id, store_id, target_date, forecast_version)
        ) PARTITION BY RANGE (target_date)
    """)

    for year in range(2020, 2028):
        op.execute(f"""
            CREATE TABLE forecasts_{year} PARTITION OF forecasts
            FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
        """)

    op.execute("""
        CREATE INDEX idx_forecasts_date_brin ON forecasts USING BRIN (target_date)
        WITH (pages_per_range = 32)
    """)
    op.create_index("idx_forecasts_model_product", "forecasts", ["model_id", "product_id", "target_date"])

    # ── model_metadata — Model registry ──
    op.create_table(
        "model_metadata",
        sa.Column("model_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("model_type", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("training_start_date", sa.Date),
        sa.Column("training_end_date", sa.Date),
        sa.Column("features_used", postgresql.JSONB),
        sa.Column("hyperparameters", postgresql.JSONB),
        sa.Column("framework_version", sa.String(32)),
        sa.Column("artifact_path", sa.String(512)),
        sa.Column("training_metrics", postgresql.JSONB),
        sa.Column("created_by", sa.String(128)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("retired_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("model_name", "model_version", name="uq_model_version"),
    )

    # ── forecast_accuracy — Evaluation snapshots ──
    op.create_table(
        "forecast_accuracy",
        sa.Column("accuracy_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("model_id", sa.Integer, nullable=False),
        sa.Column("product_id", sa.Integer),
        sa.Column("store_id", sa.Integer),
        sa.Column("evaluation_date", sa.Date, nullable=False),
        sa.Column("forecast_period", postgresql.TSTZRANGE, nullable=False),
        sa.Column("horizon_days", sa.SmallInteger),
        sa.Column("mae", sa.Numeric(12, 4)),
        sa.Column("rmse", sa.Numeric(12, 4)),
        sa.Column("mape", sa.Numeric(8, 4)),
        sa.Column("bias", sa.Numeric(12, 4)),
        sa.Column("coverage_pct", sa.Numeric(6, 3)),
        sa.Column("wmape", sa.Numeric(8, 4)),
        sa.Column("mase", sa.Numeric(12, 4)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_accuracy_model_date", "forecast_accuracy", ["model_id", "evaluation_date"])

    # ── drift_metrics — Data and prediction drift monitoring ──
    op.create_table(
        "drift_metrics",
        sa.Column("drift_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("model_id", sa.Integer, nullable=False),
        sa.Column("check_timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("reference_window", postgresql.TSTZRANGE, nullable=False),
        sa.Column("current_window", postgresql.TSTZRANGE, nullable=False),
        sa.Column("feature_name", sa.String(128)),
        sa.Column("drift_method", sa.String(32)),
        sa.Column("drift_score", sa.Numeric(10, 6)),
        sa.Column("drift_threshold", sa.Numeric(10, 6)),
        sa.Column("drift_detected", sa.Boolean),
        sa.Column("prediction_psi", sa.Numeric(10, 6)),
        sa.Column("prediction_drift_detected", sa.Boolean),
        sa.Column("target_drift_score", sa.Numeric(10, 6)),
        sa.Column("target_drift_detected", sa.Boolean),
        sa.Column("null_rate", sa.Numeric(6, 4)),
        sa.Column("out_of_range_rate", sa.Numeric(6, 4)),
        sa.Column("schema_compliant", sa.Boolean, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_drift_model_time", "drift_metrics", ["model_id", "check_timestamp"])
    op.execute("""
        CREATE INDEX idx_drift_detected ON drift_metrics (drift_detected)
        WHERE drift_detected = TRUE
    """)

    # ── alerts — Automated monitoring alerts ──
    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("model_id", sa.Integer, nullable=False),
        sa.Column("alert_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("message", sa.Text),
        sa.Column("metric_details", postgresql.JSONB),
        sa.Column("acknowledged", sa.Boolean, server_default=sa.text("FALSE")),
        sa.Column("acknowledged_by", sa.String(128)),
        sa.Column("acknowledged_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop all core tables."""
    op.drop_table("alerts")
    op.drop_table("drift_metrics")
    op.drop_table("forecast_accuracy")
    op.drop_table("model_metadata")
    op.drop_table("forecasts")
    op.drop_table("actuals")

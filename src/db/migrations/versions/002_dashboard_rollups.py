"""Dashboard rollups — TimescaleDB continuous aggregates for BI performance.

Revision ID: 002
Revises: 001
Create Date: 2026-08-03
"""

from collections.abc import Sequence

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create TimescaleDB continuous aggregates for dashboard performance."""

    # Daily rollup
    op.execute("""
        CREATE MATERIALIZED VIEW actuals_daily_rollup
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', date) AS bucket,
            product_id,
            store_id,
            SUM(quantity_sold) AS total_qty,
            SUM(revenue) AS total_revenue,
            AVG(quantity_sold) AS avg_qty,
            COUNT(*) AS transaction_count
        FROM actuals
        GROUP BY bucket, product_id, store_id
    """)

    # Weekly rollup
    op.execute("""
        CREATE MATERIALIZED VIEW actuals_weekly_rollup
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('7 days', date) AS bucket,
            product_id,
            store_id,
            SUM(quantity_sold) AS total_qty,
            SUM(revenue) AS total_revenue,
            AVG(quantity_sold) AS avg_qty,
            COUNT(*) AS transaction_count
        FROM actuals
        GROUP BY bucket, product_id, store_id
    """)

    # Monthly rollup
    op.execute("""
        CREATE MATERIALIZED VIEW actuals_monthly_rollup
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('30 days', date) AS bucket,
            product_id,
            store_id,
            SUM(quantity_sold) AS total_qty,
            SUM(revenue) AS total_revenue,
            AVG(quantity_sold) AS avg_qty,
            COUNT(*) AS transaction_count
        FROM actuals
        GROUP BY bucket, product_id, store_id
    """)

    # Refresh policies (refresh every 30 min, keep 2 years)
    for view in ("actuals_daily_rollup", "actuals_weekly_rollup", "actuals_monthly_rollup"):
        op.execute(f"""
            SELECT add_continuous_aggregate_policy('{view}',
                start_offset => INTERVAL '2 days',
                end_offset => INTERVAL '1 hour',
                schedule_interval => INTERVAL '30 minutes'
            )
        """)


def downgrade() -> None:
    """Drop continuous aggregates."""
    for view in ("actuals_monthly_rollup", "actuals_weekly_rollup", "actuals_daily_rollup"):
        op.execute(f"DROP MATERIALIZED VIEW IF EXISTS {view} CASCADE")

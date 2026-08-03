"""Multi-tenant support — adds tenant_id to core tables.

Revision ID: 003
Revises: 002
Create Date: 2026-08-03
"""

from typing import Sequence, Union
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tenant_id column to core tables."""
    for table in ("actuals", "forecasts", "model_metadata", "forecast_accuracy", "drift_metrics", "alerts"):
        op.execute(f"""
            ALTER TABLE {table}
            ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64) DEFAULT 'default'
        """)
        op.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_tenant
            ON {table} (tenant_id)
        """)


def downgrade() -> None:
    """Remove tenant_id column from core tables."""
    for table in ("alerts", "drift_metrics", "forecast_accuracy", "model_metadata", "forecasts", "actuals"):
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS tenant_id")

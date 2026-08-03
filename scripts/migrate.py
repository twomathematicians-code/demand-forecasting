#!/usr/bin/env python3
"""Run Alembic database migrations.

Usage:
    python scripts/migrate.py              # Run pending migrations
    python scripts/migrate.py --revision   # Generate a new migration
    python scripts/migrate.py --downgrade  # Rollback last migration
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "src" / "db" / "migrations"


def run_alembic(command: str, *args: str) -> int:
    """Execute an Alembic command."""
    cmd = [
        sys.executable, "-m", "alembic",
        "-c", str(MIGRATIONS_DIR / "alembic.ini"),
        command,
        *args,
    ]
    return subprocess.call(cmd, cwd=str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Database migration manager")
    parser.add_argument(
        "--upgrade", action="store_true", default=True,
        help="Run pending migrations (default)"
    )
    parser.add_argument(
        "--revision", type=str, default=None, metavar="MESSAGE",
        help="Generate a new migration with the given message"
    )
    parser.add_argument(
        "--downgrade", action="store_true",
        help="Rollback the last migration"
    )
    parser.add_argument(
        "--history", action="store_true",
        help="Show migration history"
    )
    args = parser.parse_args()

    if args.downgrade:
        return run_alembic("downgrade", "-1")
    elif args.revision:
        return run_alembic("revision", "--autogenerate", "-m", args.revision)
    elif args.history:
        return run_alembic("history")
    else:
        return run_alembic("upgrade", "head")


if __name__ == "__main__":
    sys.exit(main())

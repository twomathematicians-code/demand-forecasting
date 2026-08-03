#!/usr/bin/env python3
"""Run Evidently AI drift check from the command line.

Usage:
    python scripts/run_drift_check.py --model-id 1
    python scripts/run_drift_check.py --model-id 1 --reference-days 180 --current-days 30
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitoring.drift_checker import run_drift_check, get_default_windows
from src.db.session import init_db, close_db
from src.utils.logging import setup_logging


async def main_async(args: argparse.Namespace) -> int:
    setup_logging("INFO")

    ref_start, ref_end, cur_start, cur_end = get_default_windows(
        reference_days=args.reference_days,
        current_days=args.current_days,
    )

    await init_db()

    result = await run_drift_check(
        model_id=args.model_id,
        reference_start=ref_start,
        reference_end=ref_end,
        current_start=cur_start,
        current_end=cur_end,
    )

    print(f"\n{'='*60}")
    print(f"Drift Check Results (model_id={args.model_id})")
    print(f"  Reference window: {ref_start} → {ref_end}")
    print(f"  Current window:   {cur_start} → {cur_end}")
    print(f"  Features checked:  {result['features_checked']}")
    print(f"  Drifts detected:   {result['drifts_detected']}")
    print(f"  Alerts created:    {result['alerts_created']}")
    if result.get("error"):
        print(f"  Error:             {result['error']}")
    print(f"{'='*60}")

    await close_db()
    return 0 if not result.get("error") else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Evidently AI drift check")
    parser.add_argument("--model-id", type=int, default=1, help="Model ID from model_metadata")
    parser.add_argument("--reference-days", type=int, default=90, help="Reference window in days")
    parser.add_argument("--current-days", type=int, default=30, help="Current window in days")
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()

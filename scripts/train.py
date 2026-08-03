#!/usr/bin/env python3
"""Demand forecasting training pipeline entrypoint.

Usage:
    python scripts/train.py                          # Train with synthetic data
    python scripts/train.py --data data/historical.csv   # Train on CSV
    python scripts/train.py --data data/historical.parquet  # Train on Parquet
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipelines.training_pipeline import TrainingPipeline
from src.utils.config import get_app_config
from src.utils.logging import setup_logging


def main():
    parser = argparse.ArgumentParser(description="Train demand forecasting ensemble")
    parser.add_argument(
        "--data", type=str, default=None,
        help="Path to CSV or Parquet data file (default: generate synthetic data)"
    )
    parser.add_argument(
        "--model-dir", type=str, default="models/ensemble",
        help="Directory to save trained model (default: models/ensemble)"
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to model_config.yaml (default: configs/model_config.yaml)"
    )
    args = parser.parse_args()

    setup_logging("INFO")
    config = get_app_config(args.config)

    pipeline = TrainingPipeline(config)
    result = pipeline.run(
        data_path=args.data,
        model_dir=args.model_dir,
    )

    print(f"\n{'='*60}")
    print(f"Training {'SUCCEEDED' if result['status'] == 'success' else 'FAILED'}")
    print(f"Model path: {result['model_path']}")
    if result["metrics"]:
        print(f"MAPE: {result['metrics'].get('mape', 'N/A'):.2f}%")
        print(f"RMSE: {result['metrics'].get('rmse', 'N/A'):.2f}")
        print(f"R²:   {result['metrics'].get('r2', 'N/A'):.3f}")
    if result["errors"]:
        print(f"Errors: {result['errors']}")
    print(f"{'='*60}")

    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())

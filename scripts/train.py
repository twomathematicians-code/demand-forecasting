#!/usr/bin/env python3
"""Demand forecasting training pipeline — production-ready CLI.

Usage:
    python scripts/train.py                          # Train with synthetic data
    python scripts/train.py --data data/historical.csv   # Train on CSV
    python scripts/train.py --output models/prod      # Custom output dir
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipelines.training_pipeline import TrainingPipeline
from src.utils.config import get_app_config
from src.utils.logging import setup_logging


SEP = "=" * 60
SUB = "-" * 40


def print_header(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(f"{SEP}")


def print_metric(label: str, value: str, color: str = "") -> None:
    print(f"  {label:<20} {value}")


def print_status(passed: bool, label: str) -> None:
    icon = "PASS" if passed else "FAIL"
    print(f"  [{icon}] {label}")


def main():
    parser = argparse.ArgumentParser(
        description="Train demand forecasting ensemble (Prophet + SARIMA + LightGBM + CNN-LSTM)"
    )
    parser.add_argument("--data", type=str, default=None, help="Path to CSV/Parquet data file")
    parser.add_argument("--output", type=str, default="models/ensemble", help="Model output directory")
    parser.add_argument("--config", type=str, default=None, help="Path to model_config.yaml")
    args = parser.parse_args()

    setup_logging("WARNING")

    print_header("Demand Forecasting — Model Training Pipeline")
    print(f"  Started:    {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Data:       {args.data or 'synthetic (auto-generated)'}")
    print(f"  Output:     {args.output}")
    print(f"{SUB}")

    t0 = time.time()

    # Load config
    config = get_app_config(args.config)
    print(f"  Config OK   horizon={config.demand.default_horizon}d, "
          f"lgb={config.models.lightgbm.n_estimators} trees, "
          f"cnn_epochs={config.models.cnn_lstm.epochs}")

    # Train
    print(f"\n  Training ensemble (Prophet + SARIMA + LightGBM + CNN-LSTM)...")
    pipeline = TrainingPipeline(config)
    result = pipeline.run(data_path=args.data, model_dir=args.output)

    elapsed = time.time() - t0

    # Results
    print(f"\n{SUB}")
    print(f"  Status:     {result['status'].upper()}")
    print(f"  Duration:   {elapsed:.1f}s")

    if result["metrics"]:
        m = result["metrics"]
        print(f"\n  ── Ensemble Metrics ──")
        print_metric("MAPE", f"{m.get('mape', 'N/A'):.2f}%")
        print_metric("RMSE", f"{m.get('rmse', 'N/A'):.2f}")
        print_metric("R-squared", f"{m.get('r2', 'N/A'):.3f}")
        print(f"\n  ── Per-Model MAPE ──")
        print_metric("Prophet", f"{m.get('prophet_mape', 'N/A'):.2f}%")
        print_metric("SARIMA", f"{m.get('sarima_mape', 'N/A'):.2f}%")
        print_metric("LightGBM", f"{m.get('lgb_mape', 'N/A'):.2f}%")
        print_metric("CNN-LSTM", f"{m.get('cnn_mape', 'N/A'):.2f}%")

    print(f"\n  ── Quality Gates ──")
    print_status(result["quality_gates_passed"], "Quality gates")
    if result["errors"]:
        for err in result["errors"]:
            print(f"    ! {err}")

    print(f"\n  Model saved to: {result['model_path']}")
    print(f"{SEP}\n")

    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())

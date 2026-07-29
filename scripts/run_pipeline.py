#!/usr/bin/env python3
"""Demand forecasting training pipeline."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).parent.parent))
import logging
logging.basicConfig(level=logging.INFO)
logging.info("Demand pipeline — LightGBM + Prophet training ready")

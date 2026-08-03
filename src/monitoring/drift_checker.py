"""Evidently AI drift monitoring — scheduled drift checks → drift_metrics + alerts tables."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

from src.db.queries import INSERT_ALERT, INSERT_DRIFT
from src.db.session import get_db

log = logging.getLogger(__name__)

DRIFT_THRESHOLD = 0.1  # Evidently default for distance-based tests


async def run_drift_check(
    model_id: int,
    reference_start: str,
    reference_end: str,
    current_start: str,
    current_end: str,
) -> dict:
    """Run Evidently drift report comparing reference vs current window.

    Args:
        model_id: The model ID to associate drift results with.
        reference_start/end: ISO date strings for the reference (training) period.
        current_start/end: ISO date strings for the current (monitoring) period.

    Returns:
        Dict with keys: features_checked, drifts_detected, alerts_created, error (if any).
    """
    result = {"features_checked": 0, "drifts_detected": 0, "alerts_created": 0, "error": None}

    try:
        from evidently import ColumnMapping
        from evidently.metric_preset import DataDriftPreset, DataQualityPreset
        from evidently.report import Report
    except ImportError:
        result["error"] = "evidently not installed"
        log.warning("Evidently AI not installed. Drift check skipped.")
        return result

    db = get_db()
    if not db.is_connected:
        await db.connect()

    # Load reference and current data
    ref_rows = await db.fetch(
        "SELECT product_id, store_id, date, quantity_sold, revenue, is_promotion "
        "FROM actuals WHERE date >= $1 AND date <= $2 ORDER BY date",
        reference_start, reference_end,
    )
    cur_rows = await db.fetch(
        "SELECT product_id, store_id, date, quantity_sold, revenue, is_promotion "
        "FROM actuals WHERE date >= $1 AND date <= $2 ORDER BY date",
        current_start, current_end,
    )

    ref = pd.DataFrame(ref_rows)
    cur = pd.DataFrame(cur_rows)

    if len(ref) < 30 or len(cur) < 30:
        result["error"] = f"Insufficient data: ref={len(ref)}, cur={len(cur)}"
        log.warning("Insufficient data for drift check: ref=%d, cur=%d", len(ref), len(cur))
        return result

    # Configure Evidently
    column_mapping = ColumnMapping(
        numerical_features=["quantity_sold", "revenue"],
        categorical_features=["is_promotion"],
        target="quantity_sold",
    )

    # Run report
    report = Report(metrics=[DataDriftPreset(), DataQualityPreset()])
    report.run(reference_data=ref, current_data=cur, column_mapping=column_mapping)
    report_dict = report.as_dict()

    # Parse drift results
    metrics = report_dict.get("metrics", [])
    check_time = datetime.now(timezone.utc)

    for metric in metrics:
        if metric.get("metric") != "DataDriftTable":
            continue

        drift_by_columns = metric.get("result", {}).get("drift_by_columns", {})
        for feature_name, drift_info in drift_by_columns.items():
            drift_score = drift_info.get("drift_score", 0)
            drift_detected = drift_info.get("drift_detected", False)

            result["features_checked"] += 1

            # Store in drift_metrics
            await db.execute(
                INSERT_DRIFT,
                model_id,
                check_time,
                reference_start, reference_end,
                current_start, current_end,
                feature_name,
                drift_info.get("stattest_name", "psi"),
                drift_score,
                DRIFT_THRESHOLD,
                drift_detected,
                None, False, None, False,  # prediction/target drift placeholders
                None, None, True,
            )

            # Trigger alert if drift detected
            if drift_detected:
                result["drifts_detected"] += 1
                severity = "HIGH" if drift_score > 0.3 else "MEDIUM"
                await db.execute(
                    INSERT_ALERT,
                    model_id,
                    "DATA_DRIFT",
                    severity,
                    f"Drift detected: '{feature_name}' (score={drift_score:.4f}, method={drift_info.get('stattest_name', 'psi')})",
                    {"feature": feature_name, "drift_score": drift_score},
                )
                result["alerts_created"] += 1
                log.warning("ALERT: Data drift on '%s' (score=%.4f)", feature_name, drift_score)

    log.info("Drift check completed: %d features, %d drifts, %d alerts",
             result["features_checked"], result["drifts_detected"], result["alerts_created"])
    return result


def get_default_windows(reference_days: int = 90, current_days: int = 30) -> tuple[str, str, str, str]:
    """Compute default reference and current windows relative to today."""
    now = datetime.now(timezone.utc)
    current_end = now.strftime("%Y-%m-%d")
    current_start = (now - timedelta(days=current_days)).strftime("%Y-%m-%d")
    reference_end = (now - timedelta(days=current_days + 1)).strftime("%Y-%m-%d")
    reference_start = (now - timedelta(days=current_days + reference_days)).strftime("%Y-%m-%d")
    return reference_start, reference_end, current_start, current_end

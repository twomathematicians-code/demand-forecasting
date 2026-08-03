"""Forecast accuracy metrics for model evaluation."""

from __future__ import annotations

import numpy as np


def mean_absolute_error(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(np.mean(np.abs(actual - predicted)))


def root_mean_squared_error(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def mean_absolute_percentage_error(actual: np.ndarray, predicted: np.ndarray, epsilon: float = 1e-8) -> float:
    """Mean Absolute Percentage Error. Returns percentage (0-100)."""
    mask = np.abs(actual) > epsilon
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def symmetric_mape(actual: np.ndarray, predicted: np.ndarray, epsilon: float = 1e-8) -> float:
    """Symmetric Mean Absolute Percentage Error (0-200%)."""
    denom = np.abs(actual) + np.abs(predicted)
    mask = denom > epsilon
    if not mask.any():
        return float("nan")
    return float(np.mean(2 * np.abs(actual[mask] - predicted[mask]) / denom[mask]) * 100)


def weighted_mape(actual: np.ndarray, predicted: np.ndarray, weights: np.ndarray | None = None) -> float:
    """Weighted MAPE — weights errors by actual value (revenue-weighted).

    If no weights provided, uses |actual| as the weight.
    """
    if weights is None:
        weights = np.abs(actual)
    total_weight = weights.sum()
    if total_weight == 0:
        return float("nan")
    return float(np.sum(weights * np.abs(actual - predicted)) / total_weight)


def mean_absolute_scaled_error(
    actual: np.ndarray, predicted: np.ndarray, naive_predicted: np.ndarray, epsilon: float = 1e-8
) -> float:
    """Mean Absolute Scaled Error — scale-independent, compare to naive baseline.

    MASE < 1 means the model is better than naive.
    """
    mae_model = np.mean(np.abs(actual - predicted))
    mae_naive = np.mean(np.abs(actual - naive_predicted))
    if mae_naive < epsilon:
        return float("inf")
    return float(mae_model / mae_naive)


def mean_percentage_error(actual: np.ndarray, predicted: np.ndarray, epsilon: float = 1e-8) -> float:
    """Mean Percentage Error — positive = over-forecast, negative = under-forecast."""
    mask = np.abs(actual) > epsilon
    if not mask.any():
        return float("nan")
    return float(np.mean((actual[mask] - predicted[mask]) / actual[mask]) * 100)


def r_squared(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Coefficient of determination R-squared."""
    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return float(1 - ss_res / ss_tot)


def prediction_interval_coverage(actual: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    """Fraction of actual values that fall within the prediction interval."""
    covered = (actual >= lower) & (actual <= upper)
    return float(covered.mean())


def compute_all_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
    lower: np.ndarray | None = None,
    upper: np.ndarray | None = None,
    naive_predicted: np.ndarray | None = None,
    weights: np.ndarray | None = None,
) -> dict:
    """Compute a complete suite of forecast accuracy metrics.

    Args:
        actual: Ground truth values.
        predicted: Forecast values.
        lower: Lower prediction interval bound (optional).
        upper: Upper prediction interval bound (optional).
        naive_predicted: Naive forecast values for MASE (optional). Defaults to shifted actual.
        weights: Per-sample weights for wMAPE. Defaults to |actual|.

    Returns:
        Dictionary of metric_name -> value.
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    mask = np.isfinite(actual) & np.isfinite(predicted)
    a, p = actual[mask], predicted[mask]

    if len(a) == 0:
        return {"error": "No valid (actual, predicted) pairs"}

    if naive_predicted is None:
        naive_predicted = np.roll(a, 1)
        naive_predicted[0] = a[0]

    metrics = {
        "mae": mean_absolute_error(a, p),
        "rmse": root_mean_squared_error(a, p),
        "mape": mean_absolute_percentage_error(a, p),
        "smape": symmetric_mape(a, p),
        "wmape": weighted_mape(a, p, weights),
        "mase": mean_absolute_scaled_error(a, p, naive_predicted),
        "mpe": mean_percentage_error(a, p),
        "r2": r_squared(a, p),
        "n_samples": len(a),
    }

    if lower is not None and upper is not None:
        lower_arr = np.asarray(lower, dtype=float)[mask]
        upper_arr = np.asarray(upper, dtype=float)[mask]
        metrics["coverage_pct"] = prediction_interval_coverage(a, lower_arr, upper_arr)

    return metrics


def quality_gates_passed(metrics: dict, thresholds: dict) -> tuple[bool, list[str]]:
    """Check if metrics pass quality gate thresholds.

    Args:
        metrics: Output from compute_all_metrics().
        thresholds: Dict of metric_name -> threshold. For mape/bias, value is max allowed.
                    For coverage_pct/r2, value is min required.

    Returns:
        Tuple of (passed: bool, failures: list of str messages).
    """
    failures = []
    checks = {
        "mape": ("lt", "MAPE {:.2f}% exceeds threshold {:.2f}%"),
        "wmape": ("lt", "wMAPE {:.2f}% exceeds threshold {:.2f}%"),
        "mpe": ("abs_lt", "Bias |{:.2f}%| exceeds threshold {:.2f}%"),
        "rmse": ("lt", "RMSE {:.2f} exceeds threshold {:.2f}"),
        "coverage_pct": ("gt", "Coverage {:.2%} below threshold {:.2%}"),
        "r2": ("gt", "R² {:.3f} below threshold {:.3f}"),
    }

    for metric, (op, msg) in checks.items():
        if metric not in metrics or metric not in thresholds:
            continue
        val = metrics[metric]
        thresh = thresholds[metric]

        if op == "lt" and val > thresh or op == "gt" and val < thresh or op == "abs_lt" and abs(val) > thresh:
            failures.append(msg.format(val, thresh))

    return len(failures) == 0, failures

"""Named parameterized SQL queries for demand forecasting database operations."""

# ═══════════════════════════════════════════════════════════════════
# actuals — Ground-truth historical demand
# ═══════════════════════════════════════════════════════════════════

INSERT_ACTUALS = """
    INSERT INTO actuals (product_id, store_id, date, quantity_sold, revenue, is_promotion)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (product_id, store_id, date) DO UPDATE
    SET quantity_sold = EXCLUDED.quantity_sold,
        revenue = EXCLUDED.revenue,
        is_promotion = EXCLUDED.is_promotion,
        ingested_at = now()
"""

UPSERT_ACTUALS_BATCH = """
    INSERT INTO actuals (product_id, store_id, date, quantity_sold, revenue, is_promotion)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (product_id, store_id, date) DO UPDATE
    SET quantity_sold = actuals.quantity_sold + EXCLUDED.quantity_sold,
        revenue = COALESCE(EXCLUDED.revenue, actuals.revenue),
        ingested_at = now()
"""

GET_ACTUALS_BY_PRODUCT = """
    SELECT date, quantity_sold, revenue, is_promotion
    FROM actuals
    WHERE product_id = $1
      AND date >= $2
      AND date <= $3
    ORDER BY date
"""

GET_ACTUALS_DATE_RANGE = """
    SELECT product_id, store_id, date, quantity_sold, revenue, is_promotion
    FROM actuals
    WHERE date >= $1 AND date <= $2
    ORDER BY date
"""

GET_DISTINCT_PRODUCTS = """
    SELECT DISTINCT product_id
    FROM actuals
    WHERE date >= $1
    ORDER BY product_id
"""

GET_PRODUCT_DATE_RANGE = """
    SELECT MIN(date) AS min_date, MAX(date) AS max_date, COUNT(*) AS row_count
    FROM actuals
    WHERE product_id = $1
"""

# ═══════════════════════════════════════════════════════════════════
# forecasts — Model predictions
# ═══════════════════════════════════════════════════════════════════

INSERT_FORECAST = """
    INSERT INTO forecasts (model_id, product_id, store_id, forecast_date, target_date,
                           horizon_days, predicted_qty, yhat_lower, yhat_upper, forecast_version)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    ON CONFLICT (model_id, product_id, store_id, target_date, forecast_version)
    DO UPDATE SET predicted_qty = EXCLUDED.predicted_qty,
                  yhat_lower = EXCLUDED.yhat_lower,
                  yhat_upper = EXCLUDED.yhat_upper,
                  forecast_date = EXCLUDED.forecast_date
"""

INSERT_FORECASTS_BATCH = """
    INSERT INTO forecasts (model_id, product_id, store_id, forecast_date, target_date,
                           horizon_days, predicted_qty, yhat_lower, yhat_upper, forecast_version)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
"""

GET_LATEST_FORECASTS = """
    SELECT DISTINCT ON (product_id, target_date)
        product_id, target_date, predicted_qty, yhat_lower, yhat_upper, forecast_version
    FROM forecasts
    WHERE model_id = $1
      AND target_date >= $2
      AND target_date <= $3
    ORDER BY product_id, target_date, forecast_date DESC
"""

# ═══════════════════════════════════════════════════════════════════
# model_metadata — Model registry
# ═══════════════════════════════════════════════════════════════════

INSERT_MODEL_METADATA = """
    INSERT INTO model_metadata (model_name, model_type, model_version, status,
                                training_start_date, training_end_date,
                                features_used, hyperparameters, framework_version,
                                artifact_path, training_metrics, created_by)
    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9, $10, $11::jsonb, $12)
    RETURNING model_id
"""

UPDATE_MODEL_STATUS = """
    UPDATE model_metadata
    SET status = $2,
        retired_at = CASE WHEN $2 = 'retired' THEN now() ELSE retired_at END
    WHERE model_id = $1
"""

GET_ACTIVE_MODEL = """
    SELECT model_id, model_name, model_type, model_version, artifact_path,
           training_metrics, hyperparameters, features_used
    FROM model_metadata
    WHERE model_type = $1 AND status = 'active'
    ORDER BY created_at DESC
    LIMIT 1
"""

GET_MODEL_BY_VERSION = """
    SELECT model_id, model_name, model_type, model_version, artifact_path,
           training_metrics, hyperparameters, features_used, status
    FROM model_metadata
    WHERE model_name = $1 AND model_version = $2
"""

LIST_MODELS = """
    SELECT model_id, model_name, model_type, model_version, status,
           training_metrics, created_at
    FROM model_metadata
    ORDER BY created_at DESC
    LIMIT $1 OFFSET $2
"""

# ═══════════════════════════════════════════════════════════════════
# forecast_accuracy — Evaluation snapshots
# ═══════════════════════════════════════════════════════════════════

INSERT_ACCURACY = """
    INSERT INTO forecast_accuracy (model_id, product_id, store_id, evaluation_date,
                                   forecast_period, horizon_days,
                                   mae, rmse, mape, bias, coverage_pct, wmape, mase)
    VALUES ($1, $2, $3, $4, tstzrange($5, $6), $7, $8, $9, $10, $11, $12, $13, $14)
"""

GET_ACCURACY_HISTORY = """
    SELECT evaluation_date, horizon_days, mae, rmse, mape, bias, wmape, mase, coverage_pct
    FROM forecast_accuracy
    WHERE model_id = $1
    ORDER BY evaluation_date DESC
    LIMIT $2
"""

# ═══════════════════════════════════════════════════════════════════
# drift_metrics — Data and prediction drift
# ═══════════════════════════════════════════════════════════════════

INSERT_DRIFT = """
    INSERT INTO drift_metrics (model_id, check_timestamp, reference_window, current_window,
                               feature_name, drift_method, drift_score, drift_threshold,
                               drift_detected, prediction_psi, prediction_drift_detected,
                               target_drift_score, target_drift_detected,
                               null_rate, out_of_range_rate, schema_compliant)
    VALUES ($1, $2, tstzrange($3, $4), tstzrange($5, $6),
            $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
"""

GET_LATEST_DRIFT = """
    SELECT * FROM drift_metrics
    WHERE model_id = $1
    ORDER BY check_timestamp DESC
    LIMIT 1
"""

# ═══════════════════════════════════════════════════════════════════
# alerts — Automated monitoring alerts
# ═══════════════════════════════════════════════════════════════════

INSERT_ALERT = """
    INSERT INTO alerts (model_id, alert_type, severity, message, metric_details)
    VALUES ($1, $2, $3, $4, $5::jsonb)
    RETURNING alert_id
"""

ACKNOWLEDGE_ALERT = """
    UPDATE alerts
    SET acknowledged = TRUE, acknowledged_by = $2, acknowledged_at = now()
    WHERE alert_id = $1
"""

GET_ACTIVE_ALERTS = """
    SELECT alert_id, model_id, alert_type, severity, message, metric_details, created_at
    FROM alerts
    WHERE acknowledged = FALSE
    ORDER BY
        CASE severity
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            WHEN 'LOW' THEN 4
        END,
        created_at DESC
"""

# ═══════════════════════════════════════════════════════════════════
# Dashboard — Aggregation queries (Phase 2)
# ═══════════════════════════════════════════════════════════════════

DASHBOARD_SUMMARY = """
    SELECT
        COALESCE(SUM(total_qty), 0) AS total_demand,
        COALESCE(SUM(total_revenue), 0) AS total_revenue,
        COALESCE(AVG(avg_qty), 0) AS avg_daily_demand,
        COUNT(DISTINCT product_id) AS active_products
    FROM actuals_daily_rollup
    WHERE bucket >= $1 AND bucket <= $2
"""

DASHBOARD_TOP_PRODUCTS = """
    SELECT
        product_id,
        SUM(total_qty) AS total_qty,
        SUM(total_revenue) AS total_revenue
    FROM actuals_daily_rollup
    WHERE bucket >= $1 AND bucket <= $2
    GROUP BY product_id
    ORDER BY total_revenue DESC
    LIMIT $3
"""

DASHBOARD_TREND = """
    SELECT
        bucket,
        SUM(total_qty) AS total_qty,
        SUM(total_revenue) AS total_revenue,
        AVG(avg_qty) AS avg_qty
    FROM {}
    WHERE bucket >= $1 AND bucket <= $2
    GROUP BY bucket
    ORDER BY bucket
"""

FORECAST_VS_ACTUAL = """
    SELECT
        f.target_date,
        f.predicted_qty,
        COALESCE(a.quantity_sold, 0) AS actual_qty,
        (f.predicted_qty - COALESCE(a.quantity_sold, 0)) AS error,
        f.yhat_lower,
        f.yhat_upper
    FROM forecasts f
    LEFT JOIN actuals a
        ON f.product_id = a.product_id
        AND f.target_date = a.date
        AND f.store_id = a.store_id
    WHERE f.model_id = $1
      AND f.target_date >= $2
      AND f.target_date <= $3
      AND ($4::int IS NULL OR f.product_id = $4)
    ORDER BY f.target_date
"""

DASHBOARD_ACCURACY_TREND = """
    SELECT
        evaluation_date,
        horizon_days,
        mae,
        rmse,
        mape,
        bias,
        wmape
    FROM forecast_accuracy
    WHERE model_id = $1
      AND evaluation_date >= $2
    ORDER BY evaluation_date DESC
    LIMIT $3
"""

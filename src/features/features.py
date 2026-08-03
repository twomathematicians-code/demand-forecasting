"""Feature engineering for demand forecasting.

Produces temporal, calendar, weather, and cluster features from raw demand data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.config import FeatureConfig


class FeatureEngineer:
    """Transforms raw demand time series into model-ready feature matrices.

    Usage:
        engineer = FeatureEngineer(config)
        X, y = engineer.fit_transform(df)
        X_new = engineer.transform(new_df)   # inference only — do not refit
    """

    def __init__(self, config: FeatureConfig | None = None):
        self.config = config or FeatureConfig()
        self._feature_names: list[str] = []
        self._fitted: bool = False
        self._y_mean: float = 0.0
        self._y_std: float = 1.0

    @property
    def feature_names(self) -> list[str]:
        """Return the ordered list of feature names after fit."""
        return self._feature_names

    # ── Public API ──────────────────────────────────────────

    def fit_transform(self, df: pd.DataFrame, target_col: str = "quantity_sold") -> tuple[pd.DataFrame, pd.Series]:
        """Fit the feature engineer on historical data and return (X, y).

        Args:
            df: DataFrame with columns ['date', 'product_id', target_col, ...].
            target_col: Name of the column to predict.

        Returns:
            Tuple of (feature DataFrame X, target Series y).
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        # Build features
        X = self._build_all_features(df)

        # Target
        y = df[target_col].astype(float)

        # Store normalization params for transform()
        self._y_mean = y.mean()
        self._y_std = y.std() or 1.0
        self._feature_names = list(X.columns)
        self._fitted = True

        # Drop rows with NaN (from lag features)
        valid = X.notna().all(axis=1) & y.notna()
        return X.loc[valid], y.loc[valid]

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build features from a DataFrame for inference. Does not modify fit state.

        Args:
            df: DataFrame with columns ['date', 'product_id'] + optional regressors.

        Returns:
            Feature DataFrame X with the same columns as fit_transform.
        """
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        X = self._build_all_features(df)
        X = X.reindex(columns=self._feature_names, fill_value=0.0)
        return X.fillna(0.0)

    # ── Feature Builders ────────────────────────────────────

    def _build_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run all feature builders and concatenate results."""
        frames = []

        if self.config.include_date_features:
            frames.append(self._build_calendar_features(df))

        # Demand-derived features (require quantity_sold)
        if "quantity_sold" in df.columns:
            frames.append(self._build_temporal_features(df))

        if self.config.include_cluster_features and "quantity_sold" in df.columns:
            frames.append(self._build_cluster_features(df))

        # Weather features built if columns present
        weather_cols = [c for c in df.columns if c in ("temperature", "precipitation", "humidity", "wind_speed")]
        if weather_cols:
            frames.append(self._build_weather_features(df))

        # Combine + add raw regressors
        result = pd.concat(frames, axis=1) if frames else pd.DataFrame(index=df.index)
        result["date_ordinal"] = df["date"].map(pd.Timestamp.toordinal).astype(float)
        return result

    def _build_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create lag and rolling features from the demand column."""
        out = pd.DataFrame(index=df.index)
        y = df["quantity_sold"]

        for lag in self.config.lag_periods:
            out[f"lag_{lag}"] = y.shift(lag)

        for w in self.config.rolling_windows:
            rolled = y.shift(1).rolling(window=w, min_periods=max(1, w // 2))
            for stat in self.config.rolling_stats:
                col = f"rolling_{w}d_{stat}"
                if stat == "mean":
                    out[col] = rolled.mean()
                elif stat == "std":
                    out[col] = rolled.std()
                elif stat == "min":
                    out[col] = rolled.min()
                elif stat == "max":
                    out[col] = rolled.max()

        return out

    def _build_calendar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract calendar-based features with cyclical encoding."""
        out = pd.DataFrame(index=df.index)
        d = df["date"]

        out["day_of_week"] = d.dt.dayofweek.astype(float)
        out["month"] = d.dt.month.astype(float)
        out["quarter"] = d.dt.quarter.astype(float)
        out["day_of_year"] = d.dt.dayofyear.astype(float)
        out["is_weekend"] = (d.dt.dayofweek >= 5).astype(float)
        out["is_month_start"] = d.dt.is_month_start.astype(float)
        out["is_month_end"] = d.dt.is_month_end.astype(float)

        if self.config.cyclical_encoding:
            out["dow_sin"] = np.sin(2 * np.pi * out["day_of_week"] / 7)
            out["dow_cos"] = np.cos(2 * np.pi * out["day_of_week"] / 7)
            out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12)
            out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12)
            out["doy_sin"] = np.sin(2 * np.pi * out["day_of_year"] / 365.25)
            out["doy_cos"] = np.cos(2 * np.pi * out["day_of_year"] / 365.25)

        return out

    def _build_weather_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build HDD/CDD and rolling weather statistics."""
        out = pd.DataFrame(index=df.index)

        if "temperature" in df.columns:
            temp = df["temperature"]
            out["hdd"] = np.maximum(0, 18.0 - temp)
            out["cdd"] = np.maximum(0, temp - 18.0)
            out["temp_range"] = temp.rolling(7, min_periods=3).max() - temp.rolling(7, min_periods=3).min()

        if "precipitation" in df.columns:
            prec = df["precipitation"]
            for w in self.config.rolling_windows if hasattr(self.config, "rolling_windows") else [7, 30]:
                out[f"precip_{w}d_cum"] = prec.rolling(w, min_periods=max(1, w // 2)).sum()

        return out

    def _build_cluster_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute demand pattern features: ADI, CV², seasonality strength."""
        out = pd.DataFrame(index=df.index)
        y = df["quantity_sold"].values

        # Rolling ADI (Average Demand Interval — intermittency measure)
        window = 30
        if len(y) >= window:
            adi_vals = []
            cv2_vals = []
            for i in range(len(y)):
                start = max(0, i - window + 1)
                segment = y[start : i + 1]
                nz = segment[segment > 0]
                if len(nz) > 1:
                    adi_vals.append(len(segment) / len(nz))
                    cv2_vals.append((nz.std() / nz.mean()) ** 2 if nz.mean() > 0 else 0.0)
                else:
                    adi_vals.append(1.0)
                    cv2_vals.append(0.0)
            out["adi_30d"] = adi_vals
            out["cv2_30d"] = cv2_vals

        return out

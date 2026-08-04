"""Electricity dashboard — REST + WebSocket endpoints.

Routes:
    GET  /api/v1/electricity/data     — Historical data query
    GET  /api/v1/electricity/predict   — Simple statistical forecast
    GET  /api/v1/electricity/summary   — KPI snapshot
    WS   /ws/electricity/live          — Real-time streaming (every ~2.5s)
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.data.electricity_loader import (
    REGION_COLORS,
    REGION_NAMES,
    get_electricity_loader,
)

log = logging.getLogger("demand.electricity.api")

router = APIRouter(prefix="/api/v1/electricity", tags=["⚡ Electricity"])


# ── Helpers ──────────────────────────────────────────────

def _loader():
    return get_electricity_loader()


def _fmt_ts(val) -> str:
    """Convert a pandas/datetime value to ISO string."""
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


# ═══════════════════════════════════════════════════════════
# REST Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/data")
async def get_data(
    region: str = Query(default=None, description="Region code: N, NE, S, SE (omit for all)"),
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history"),
):
    """Return historical electricity demand data.

    Args:
        region: Filter to one region (N, NE, S, SE). Omit for all regions.
        hours: How many hours of history to return (1–168).
    """
    loader = _loader()

    if region:
        df = loader.get_region(region.upper())
        df = df.tail(hours)
    else:
        records = loader.get_latest(region=None, hours=hours)
        # Format
        return {
            "region": "all",
            "hours": hours,
            "count": len(records),
            "data": [
                {
                    "timestamp": _fmt_ts(r["timestamp"]),
                    "region": r["region"],
                    "demand_mw": float(r["demand_mw"]),
                }
                for r in records
            ],
        }

    return {
        "region": region.upper(),
        "hours": hours,
        "count": len(df),
        "data": [
            {
                "timestamp": _fmt_ts(row["timestamp"]),
                "region": region.upper(),
                "demand_mw": float(row["demand_mw"]),
            }
            for _, row in df.iterrows()
        ],
    }


@router.get("/predict")
async def predict(
    region: str = Query(default="SE", description="Region code: N, NE, S, SE"),
    hours: int = Query(default=24, ge=1, le=48, description="Forecast horizon in hours"),
    confidence: float = Query(default=0.9, description="Confidence level: 0.8, 0.9, 0.95"),
):
    """Simple statistical forecast using linear trend + seasonal pattern.

    Returns predicted demand with upper/lower confidence bounds.
    """
    loader = _loader()
    region = region.upper()
    if region not in REGION_NAMES:
        return {"error": f"Unknown region: {region}. Use one of: {list(REGION_NAMES.keys())}"}

    predictions = loader.predict(region=region, hours=hours, confidence=confidence)
    return {
        "region": region,
        "region_name": REGION_NAMES[region],
        "hours": hours,
        "confidence": confidence,
        "predictions": predictions,
    }


@router.get("/summary")
async def summary():
    """KPI snapshot of current electricity demand across all Brazilian regions."""
    loader = _loader()
    data = loader.get_summary()

    # Add human-readable timestamp
    ts = data["timestamp"]
    if hasattr(ts, "strftime"):
        data["timestamp_str"] = ts.strftime("%Y-%m-%d %H:%M")
    else:
        data["timestamp_str"] = str(ts)

    return data


# ═══════════════════════════════════════════════════════════
# WebSocket — Live Streaming
# ═══════════════════════════════════════════════════════════

@router.websocket("/ws/electricity/live")
async def electricity_live(websocket: WebSocket):
    """Real-time electricity demand stream.

    Pushes simulated live data points every ~2.5 seconds by cycling
    through the historical dataset. All 4 regions are broadcast per tick.

    Message format:
        {
            "type": "tick",
            "timestamp": "2025-01-15T14:00:00",
            "data": {
                "N":  {"demand_mw": 5123.4},
                "NE": {"demand_mw": 10432.1},
                "S":  {"demand_mw": 11201.8},
                "SE": {"demand_mw": 34210.5}
            },
            "totals": {
                "national_mw": 60967.8,
                "peak_region": "SE"
            },
            "elapsed_s": 42,
            "tick": 17
        }
    """
    await websocket.accept()

    loader = _loader()
    df = loader.get_data()

    if df.empty:
        await websocket.send_json({"type": "error", "message": "No data available"})
        await websocket.close()
        return

    # Build a sequential index cycling through the dataset
    unique_timestamps = sorted(df["timestamp"].unique())
    total_ticks = len(unique_timestamps)
    tick_idx = 0
    start_time = time.time()

    log.info("Electricity WebSocket client connected (dataset: %d timestamps)", total_ticks)

    try:
        while True:
            # Get current timestamp from the cycle
            current_ts = unique_timestamps[tick_idx % total_ticks]
            tick_rows = df[df["timestamp"] == current_ts]

            # Build per-region data
            region_data = {}
            peak_region = ""
            peak_val = 0
            total_mw = 0

            for _, row in tick_rows.iterrows():
                r = row["region"]
                val = float(row["demand_mw"])
                region_data[r] = {
                    "demand_mw": round(val, 1),
                    "name": REGION_NAMES.get(r, r),
                    "color": REGION_COLORS.get(r, "#94a3b8"),
                }
                total_mw += val
                if val > peak_val:
                    peak_val = val
                    peak_region = r

            elapsed = round(time.time() - start_time, 1)
            tick_num = tick_idx + 1

            message = {
                "type": "tick",
                "timestamp": _fmt_ts(current_ts),
                "data": region_data,
                "totals": {
                    "national_mw": round(total_mw, 1),
                    "peak_region": peak_region,
                    "peak_mw": round(peak_val, 1),
                },
                "elapsed_s": elapsed,
                "tick": tick_num,
            }

            await websocket.send_json(message)

            tick_idx += 1

            # Sleep ~2.5s between pushes
            await asyncio.sleep(2.5)

    except WebSocketDisconnect:
        log.info("Electricity WebSocket client disconnected after %d ticks", tick_idx)
    except Exception as e:
        log.warning("Electricity WebSocket error: %s", e)
        try:
            await websocket.close()
        except Exception:
            pass

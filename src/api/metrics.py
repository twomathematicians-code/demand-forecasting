"""Prometheus metrics endpoint for monitoring."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import APIRouter, Response

router = APIRouter(tags=["📊 Metrics"])

# Simple in-process metrics (replace with prometheus_client in production)
_metrics: dict[str, list[float]] = defaultdict(list)
_request_counts: dict[str, int] = defaultdict(int)
_start_time = time.time()


def record_request(method: str, path: str, duration_ms: float, status: int):
    """Record a request for metrics."""
    key = f"{method} {path}"
    _metrics[f"{key}_duration_ms"].append(duration_ms)
    _request_counts[f"{key}:{status}"] += 1
    _request_counts[f"{key}:total"] += 1


@router.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint.

    Returns plain text metrics in Prometheus exposition format.
    Scraped by Prometheus/Grafana for monitoring dashboards.
    """
    lines = []

    # Uptime
    uptime = time.time() - _start_time
    lines.append(f"# HELP app_uptime_seconds Application uptime")
    lines.append(f"# TYPE app_uptime_seconds gauge")
    lines.append(f"app_uptime_seconds {uptime:.1f}")

    # Request counts
    lines.append(f"# HELP app_requests_total Total requests by endpoint and status")
    lines.append(f"# TYPE app_requests_total counter")
    for key, count in sorted(_request_counts.items()):
        safe_key = key.replace(" ", "_").replace(":", "_").replace("/", "_")
        lines.append(f'app_requests_total{{endpoint="{safe_key}"}} {count}')

    # Request durations (P50, P95, P99)
    lines.append(f"# HELP app_request_duration_ms Request duration in ms")
    lines.append(f"# TYPE app_request_duration_ms summary")
    for key, durations in sorted(_metrics.items()):
        if not durations:
            continue
        sorted_durs = sorted(durations)
        safe_key = key.replace(" ", "_").replace("/", "_")
        p50 = sorted_durs[int(len(sorted_durs) * 0.5)]
        p95 = sorted_durs[int(len(sorted_durs) * 0.95)]
        p99 = sorted_durs[int(len(sorted_durs) * 0.99)]
        lines.append(f'app_request_duration_ms{{endpoint="{safe_key}",quantile="0.5"}} {p50:.1f}')
        lines.append(f'app_request_duration_ms{{endpoint="{safe_key}",quantile="0.95"}} {p95:.1f}')
        lines.append(f'app_request_duration_ms{{endpoint="{safe_key}",quantile="0.99"}} {p99:.1f}')

    return Response(content="\n".join(lines) + "\n", media_type="text/plain")

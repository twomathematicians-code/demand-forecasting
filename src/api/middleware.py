"""Production middleware: rate limiting, request IDs, and structured error handling."""

from __future__ import annotations

import time
import uuid
import logging
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger("demand.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID header for request tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter (per-IP token bucket).

    Production: replace with Redis-backed implementation.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health/websocket/admin endpoints
        path = request.url.path
        if any(skip in path for skip in ("/health", "/ws/", "/admin/")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        cutoff = now - self.window_seconds
        self._buckets[client_ip] = [t for t in self._buckets[client_ip] if t > cutoff]

        if len(self._buckets[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded: {self.max_requests} requests per {self.window_seconds}s",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._buckets[client_ip].append(now)
        return await call_next(request)


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler with structured error responses."""
    request_id = getattr(request.state, "request_id", "unknown")

    if hasattr(exc, "status_code"):
        status_code = exc.status_code
        detail = exc.detail if hasattr(exc, "detail") else str(exc)
    else:
        status_code = 500
        detail = "Internal server error"

    log.error(
        "Request failed: method=%s path=%s status=%d request_id=%s error=%s",
        request.method, request.url.path, status_code, request_id, str(exc),
        exc_info=status_code == 500,
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": status_code,
                "message": detail if status_code != 500 else "Internal server error",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
    )


class StructuredLogMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response: Response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        log.info(
            "%s %s → %d (%.1fms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            getattr(request.state, "request_id", "-"),
        )
        return response

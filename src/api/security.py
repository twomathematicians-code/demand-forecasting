"""Production security middleware: secure headers, CORS tightening, HTTPS enforcement."""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Cache-Control": "no-store, max-age=0",
        }

        # Don't cache API responses by default
        if request.url.path.startswith("/api/"):
            headers["Cache-Control"] = "no-store, max-age=0"

        for key, value in headers.items():
            if key not in response.headers:
                response.headers[key] = value

        return response


class TrustedHostMiddleware(BaseHTTPMiddleware):
    """Reject requests from untrusted hosts (DNS rebinding protection).

    In production, only accept requests from known domains.
    """

    def __init__(self, app, allowed_hosts: list[str] | None = None):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or [
            "localhost",
            "127.0.0.1",
            "demand-forecast-api.onrender.com",
            ".onrender.com",
        ]

    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "").split(":")[0]  # strip port

        # Allow health checks from internal Render infrastructure
        if request.url.path == "/api/v1/health" or host in ("127.0.0.1", "localhost"):
            return await call_next(request)

        # Check if host matches allowed patterns
        allowed = any(
            host == pattern or (pattern.startswith(".") and host.endswith(pattern))
            for pattern in self.allowed_hosts
        )

        if not allowed:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=421,
                content={"detail": "Misdirected request — host not allowed"},
            )

        return await call_next(request)

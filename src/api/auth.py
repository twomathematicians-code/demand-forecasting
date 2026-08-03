"""API authentication — simple API key validation."""

from __future__ import annotations

import os
import logging
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

log = logging.getLogger(__name__)

# Admin API key — set via environment variable DF_ADMIN_API_KEY
ADMIN_API_KEY = os.getenv("DF_ADMIN_API_KEY", "")

security = HTTPBearer(auto_error=False)


async def verify_admin(request: Request) -> None:
    """Verify the request has a valid admin API key.

    Usage as FastAPI dependency:
        @app.post("/admin/retrain", dependencies=[Depends(verify_admin)])
    """
    if not ADMIN_API_KEY:
        # No key configured — allow all (development mode)
        return

    credentials: HTTPAuthorizationCredentials | None = await security(request)
    if credentials is None:
        raise HTTPException(status_code=401, detail="API key required")

    if credentials.credentials != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    log.info("Admin access granted")

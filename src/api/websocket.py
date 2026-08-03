"""WebSocket routes — real-time dashboard updates and forecast streaming."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(tags=["🔌 WebSocket"])
log = logging.getLogger(__name__)


# ── Typed Messages ───────────────────────────────────────

class ForecastUpdate(BaseModel):
    type: str = "forecast_update"
    product_id: str
    horizon_days: int
    data: list[dict]
    generated_at: str


class AlertMessage(BaseModel):
    type: str = "alert"
    alert_type: str
    severity: str
    message: str
    created_at: str


class HeartbeatMessage(BaseModel):
    type: str = "heartbeat"
    timestamp: str


# ── Connection Manager ───────────────────────────────────

class WebSocketManager:
    """Manages active WebSocket connections with broadcast capability."""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self._connections[session_id] = websocket
        log.info("WebSocket connected: %s (total: %d)", session_id, len(self._connections))

    def disconnect(self, session_id: str) -> None:
        self._connections.pop(session_id, None)
        log.info("WebSocket disconnected: %s (total: %d)", session_id, len(self._connections))

    async def broadcast(self, message: BaseModel | dict) -> None:
        """Push a message to all connected clients."""
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        dead = []
        for sid, ws in self._connections.items():
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(sid)
        for sid in dead:
            self.disconnect(sid)

    async def send_to(self, session_id: str, message: BaseModel | dict) -> None:
        """Push a message to a specific client."""
        ws = self._connections.get(session_id)
        if ws is None:
            return
        payload = message.model_dump() if isinstance(message, BaseModel) else message
        try:
            await ws.send_json(payload)
        except Exception:
            self.disconnect(session_id)

    @property
    def active_count(self) -> int:
        return len(self._connections)


# ── Singleton ────────────────────────────────────────────

_manager: WebSocketManager | None = None


def get_ws_manager() -> WebSocketManager:
    global _manager
    if _manager is None:
        _manager = WebSocketManager()
    return _manager


# ── Routes ───────────────────────────────────────────────

@router.websocket("/ws/dashboard/{client_id}")
async def dashboard_websocket(websocket: WebSocket, client_id: str):
    """Live dashboard: receives forecast updates, drift alerts, and heartbeat."""
    manager = get_ws_manager()
    await manager.connect(websocket, client_id)

    async def heartbeat():
        while True:
            await asyncio.sleep(30)
            try:
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                break

    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            if msg_type == "subscribe":
                pass  # Future: per-product subscription tracking
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.warning("WebSocket error for %s: %s", client_id, e)
    finally:
        heartbeat_task.cancel()
        manager.disconnect(client_id)


@router.websocket("/ws/forecast/{product_id}")
async def forecast_live_stream(websocket: WebSocket, product_id: str):
    """Per-product forecast stream: live updates when new forecasts are generated."""
    manager = get_ws_manager()
    await manager.connect(websocket, product_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(product_id)

from __future__ import annotations

"""WebSocket connection manager for real-time transcription endpoints."""

from typing import Set

from fastapi import WebSocket

__all__ = ["ConnectionManager"]


class ConnectionManager:  # noqa: D401 – class name is explicit
    """Minimal connection pool handling connect, disconnect and broadcast."""

    def __init__(self) -> None:
        self._active: Set[WebSocket] = set()

    # ------------------------------------------------------------------
    async def connect(self, ws: WebSocket) -> None:  # noqa: D401
        await ws.accept()
        self._active.add(ws)

    # ------------------------------------------------------------------
    def disconnect(self, ws: WebSocket) -> None:  # noqa: D401
        self._active.discard(ws)

    # ------------------------------------------------------------------
    async def send(self, ws: WebSocket, message: dict) -> None:  # noqa: D401
        await ws.send_json(message)

    # ------------------------------------------------------------------
    async def broadcast(self, message: dict) -> None:  # noqa: D401
        for ws in list(self._active):
            try:
                await ws.send_json(message)
            except Exception:
                self._active.discard(ws) 
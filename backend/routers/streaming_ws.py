from __future__ import annotations

"""Generic streaming WebSocket endpoint powered by *StreamingService*.

Client connects to /ws/stream?engine=vosk (or whisper, azure_speech).
Audio chunks must be raw 16-bit LE PCM at 16-kHz mono.
Outgoing JSON mirrors the per-handler update dictionaries.
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.bootstrap import container
from src.core.interfaces.streaming_service import IStreamingService

logger = logging.getLogger("ambient_scribe")

router = APIRouter()


@router.websocket("/ws/stream")
async def websocket_stream(ws: WebSocket) -> None:  # noqa: D401
    await ws.accept()

    engine = ws.query_params.get("engine", "vosk")

    try:
        streaming: IStreamingService = container.resolve(IStreamingService)
    except Exception as exc:
        logger.error("StreamingService unavailable: %s", exc)
        await ws.close(code=1011)
        return

    session_id = streaming.start_session(engine)
    try:
        while True:
            chunk = await ws.receive_bytes()
            streaming.process_chunk(session_id, chunk)
            for update in streaming.get_updates(session_id):
                await ws.send_json(update)
    except WebSocketDisconnect:
        logger.info("Client disconnected from /ws/stream")
    except Exception as exc:
        logger.error("/ws/stream error: %s", exc)
        await ws.close(code=1011)
    finally:
        streaming.end_session(session_id) 
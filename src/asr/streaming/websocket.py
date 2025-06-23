from __future__ import annotations

"""FastAPI router providing real-time speech-to-text websockets.

This module was extracted from *backend.realtime* to live next to the
streaming handlers under *src.asr.streaming*.
It exposes a `router` object that can be included by the backend layer.
"""

import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from vosk import Model, KaldiRecognizer  # type: ignore

from ...core.container import global_container
from ...core.interfaces.config_service import IConfigurationService
from .connection_manager import ConnectionManager

logger = logging.getLogger("ambient_scribe")

__all__ = ["router"]

# ---------------------------------------------------------------------------
# Load model path from configuration or environment
# ---------------------------------------------------------------------------
try:
    config_service = global_container.resolve(IConfigurationService)
    base_dir = config_service.get("base_dir", Path("./app_data"))
except Exception:  # pragma: no cover – DI not ready during import
    base_dir = Path("./app_data")

MODELS_BASE = base_dir / "models"
try:
    _cfg = global_container.resolve(IConfigurationService)
    DEFAULT_FOLDER = _cfg.get("default_vosk_model", "small-english")  # type: ignore[arg-type]
except Exception:
    DEFAULT_FOLDER = "small-english"

MODEL_DIR = MODELS_BASE / DEFAULT_FOLDER

if not MODEL_DIR.exists():
    # Fallback to any model directory that exists
    candidates = [p for p in MODELS_BASE.iterdir() if p.is_dir()]
    if candidates:
        MODEL_DIR = candidates[0]
        logger.warning(
            "Configured Vosk model '%s' not found; falling back to '%s'",
            DEFAULT_FOLDER,
            MODEL_DIR.name,
        )
    else:
        raise RuntimeError("No Vosk models found in app_data/models – please add one.")

logger.info("Loading Vosk model for streaming WebSocket from %s", MODEL_DIR)
_VOSK_MODEL = Model(str(MODEL_DIR))
logger.info("Vosk model loaded for streaming.")

SAMPLE_RATE = 16000  # Hz – expected by small English model

router = APIRouter()

# Global connection manager instance
_connections = ConnectionManager()


@router.websocket("/ws/vosk")
async def websocket_vosk(ws: WebSocket) -> None:  # noqa: D401
    """Real-time speech-to-text WebSocket endpoint.

    The browser must stream raw 16-bit little-endian mono PCM at 16-kHz.
    Outgoing messages:
        { "type": "partial", "text": "..." }
        { "type": "final",  "text": "..." }
    """
    await _connections.connect(ws)

    # Switch model if specified via query (?model=name)
    model_param = ws.query_params.get("model")
    if model_param and model_param != "default":
        candidate_dir = MODELS_BASE / model_param
        if not candidate_dir.exists():
            await ws.close(code=4404, reason=f"Model '{model_param}' not found")
            return
        recognizer_model = Model(str(candidate_dir))
    else:
        recognizer_model = _VOSK_MODEL

    recognizer = KaldiRecognizer(recognizer_model, SAMPLE_RATE)
    recognizer.SetWords(True)

    try:
        while True:
            audio_bytes = await ws.receive_bytes()
            if recognizer.AcceptWaveform(audio_bytes):
                res = json.loads(recognizer.Result())
                await ws.send_json(
                    {
                        "type": "final",
                        "text": res.get("text", ""),
                        "result": res.get("result", []),
                    }
                )
            else:
                res = json.loads(recognizer.PartialResult())
                await ws.send_json({"type": "partial", "text": res.get("partial", "")})
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from /ws/vosk")
        _connections.disconnect(ws)
    except Exception as exc:  # pragma: no cover
        logger.error("WebSocket /ws/vosk error: %s", exc)
        await ws.close(code=1011)
        _connections.disconnect(ws) 
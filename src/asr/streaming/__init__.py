from __future__ import annotations

"""Streaming sub-package for ASR.

This exposes the real-time streaming handlers and WebSocket router used by
FastAPI.  All public symbols are re-exported here so that callers can simply
import `src.asr.streaming`.
"""

from .handlers import (
    VoskStreamingHandler,
    WhisperStreamingHandler,
    AzureSpeechStreamingHandler,
)
from .websocket import router as websocket_router

__all__ = [
    "VoskStreamingHandler",
    "WhisperStreamingHandler",
    "AzureSpeechStreamingHandler",
    "websocket_router",
] 
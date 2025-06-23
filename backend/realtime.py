from __future__ import annotations
"""DEPRECATED real-time Vosk WebSocket implementation.

The live implementation now lives in ``src.asr.streaming.websocket``.
This thin wrapper re-exports its `router` object so existing imports
continue to work while avoiding duplicate model loading.
"""

import warnings

from src.asr.streaming.websocket import router  # noqa: F401

warnings.warn(
    "`backend.realtime` is deprecated; import `src.asr.streaming.websocket` instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["router"] 
from __future__ import annotations

from contextlib import contextmanager
import logging
import os
from typing import Any
from pathlib import Path

import pyaudio

from ..core.container import global_container  # type: ignore
from ..core.interfaces.config_service import IConfigurationService

logger = logging.getLogger("ambient_scribe")


def get_audio_config() -> dict[str, Any]:
    """Return audio parameters with sane fallbacks when DI is unavailable."""
    try:
        cfg = global_container.resolve(IConfigurationService)
        return {
            "format_str": cfg.get("format_str", "paInt16"),
            "channels": int(cfg.get("channels", 1)),
            "rate": int(cfg.get("rate", 16000)),
            "chunk": int(cfg.get("chunk", 1024)),
        }
    except Exception:  # pragma: no cover – DI container not ready
        return {
            "format_str": "paInt16",
            "channels": 1,
            "rate": 16000,
            "chunk": 1024,
        }


@contextmanager
def audio_stream(p: pyaudio.PyAudio | None = None, close_pyaudio: bool = True):
    """Context-manager yielding an open input stream and its PyAudio interface."""
    stream = None
    pa_interface = p or pyaudio.PyAudio()
    cfg = get_audio_config()

    try:
        fmt = getattr(pyaudio, cfg["format_str"], pyaudio.paInt16)
        stream = pa_interface.open(
            format=fmt,
            channels=cfg["channels"],
            rate=cfg["rate"],
            input=True,
            frames_per_buffer=cfg["chunk"],
        )
        yield stream, pa_interface
    finally:
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except Exception as exc:  # pragma: no cover
                logger.error("Error closing audio stream: %s", exc)
        if close_pyaudio:
            try:
                pa_interface.terminate()
            except Exception as exc:  # pragma: no cover
                logger.error("Error terminating PyAudio: %s", exc) 
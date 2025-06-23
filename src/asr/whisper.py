from __future__ import annotations

"""DEPRECATED wrapper for WhisperTranscriber.

Implementation now lives in *src.asr.transcribers.whisper*.
"""

import warnings

from .transcribers.whisper import WhisperTranscriber  # noqa: F401

warnings.warn(
    "`src.asr.whisper` is deprecated; use `src.asr.transcribers.whisper` instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["WhisperTranscriber"]

from __future__ import annotations

"""DEPRECATED wrapper module.

The implementation has been moved to *src.asr.transcribers.vosk*.
Importing from this module will continue to work but will emit a
``DeprecationWarning``.
"""

import warnings

from .transcribers.vosk import VoskTranscriber  # noqa: F401

warnings.warn(
    "`src.asr.vosk` is deprecated; use `src.asr.transcribers.vosk` instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["VoskTranscriber"]

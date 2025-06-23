from __future__ import annotations

"""DEPRECATED wrapper for Azure transcriber modules.

Implementation moved to *src.asr.transcribers.azure*.
"""

import warnings

from .transcribers.azure_speech import AzureSpeechTranscriber  # noqa: F401
from .transcribers.azure_whisper import AzureWhisperTranscriber  # noqa: F401

warnings.warn(
    "`src.asr.azure_speech` is deprecated; use `src.asr.transcribers.azure` instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "AzureSpeechTranscriber",
    "AzureWhisperTranscriber",
]

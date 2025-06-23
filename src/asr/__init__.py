"""asr package public API with lazy attribute loading.

Heavy imports are deferred until first access to avoid circular
dependencies during application bootstrap.
"""

from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType
from typing import Any

# Public attributes that can be imported from the package root.
__all__ = [
    "transcribe_audio",
    "WhisperTranscriber",
    "VoskTranscriber",
    "AzureSpeechTranscriber",
    "AzureWhisperTranscriber",
]


_lazy_map: dict[str, tuple[str, str]] = {
    "transcribe_audio": ("asr.transcription", "transcribe_audio"),
    "WhisperTranscriber": ("asr.transcribers.whisper", "WhisperTranscriber"),
    "VoskTranscriber": ("asr.transcribers.vosk", "VoskTranscriber"),
    "AzureSpeechTranscriber": ("asr.transcribers.azure_speech", "AzureSpeechTranscriber"),
    "AzureWhisperTranscriber": ("asr.transcribers.azure_whisper", "AzureWhisperTranscriber"),
}


def __getattr__(name: str) -> Any:  # noqa: D401
    if name in _lazy_map:
        module_name, attr_name = _lazy_map[name]
        module: ModuleType = import_module(module_name)
        value = getattr(module, attr_name)
        setattr(sys.modules[__name__], name, value)
        return value
    raise AttributeError(name)

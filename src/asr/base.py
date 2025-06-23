# noqa: D401

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.core.interfaces.transcription import ITranscriber


# ------------------------------------------------------------------
# Base class implementing the common functionality of all transcribers.
# It now directly implements *ITranscriber* to guarantee interface compliance.
# ------------------------------------------------------------------


class Transcriber(ITranscriber):
    """Abstract base class for ASR transcribers."""

    @abstractmethod
    async def transcribe(self, audio_path: Path, **kwargs: Any) -> str:
        """Return a transcript for the provided audio file."""
        raise NotImplementedError

    def is_supported_format(self, file_path: Path) -> bool:
        """Return True if file_path is in a format supported by the transcriber."""
        # Default implementation - supports common audio formats
        supported_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg'}
        return file_path.suffix.lower() in supported_extensions

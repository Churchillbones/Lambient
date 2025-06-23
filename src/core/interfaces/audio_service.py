from __future__ import annotations

"""Audio service abstraction for Phase-5 pipeline."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["IAudioService"]


@runtime_checkable
class IAudioService(Protocol):  # noqa: D401
    """Core audio-processing operations exposed via DI."""

    # ------------------------------------------------------------------
    @abstractmethod
    def convert_to_wav(self, in_path: str | Path) -> Path:  # noqa: D401
        """Convert *in_path* to 16-kHz mono PCM WAV and return new path."""

    @abstractmethod
    def format_transcript_with_confidence(self, text: str, *, partial: str = "", words_info: list | None = None) -> str:  # noqa: D401,E501
        """Return HTML representation of *text* with low-confidence markup."""

    @abstractmethod
    def format_elapsed_time(self, start_time: float, current_time: float | None = None) -> str:  # noqa: D401
        """Return M:SS representation of elapsed seconds.""" 
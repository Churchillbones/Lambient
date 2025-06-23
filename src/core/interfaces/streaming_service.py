from __future__ import annotations

"""Interface for real-time audio streaming services (Phase-5)."""

from abc import ABC, abstractmethod
from typing import Any, Iterable

__all__ = ["IStreamingService"]


class IStreamingService(ABC):  # noqa: D401
    """High-level session manager for real-time ASR streaming."""

    @abstractmethod
    def start_session(self, engine: str, **options: Any) -> str:  # noqa: D401
        """Open a new streaming session and return its *session_id*."""

    @abstractmethod
    def process_chunk(self, session_id: str, chunk: bytes) -> None:  # noqa: D401
        """Feed raw PCM *chunk* into the recogniser for *session_id*."""

    @abstractmethod
    def get_updates(self, session_id: str) -> Iterable[dict]:  # noqa: D401
        """Yield pending transcription updates for *session_id*."""

    @abstractmethod
    def end_session(self, session_id: str) -> None:  # noqa: D401
        """Close the session and free resources.""" 
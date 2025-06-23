from __future__ import annotations

"""Concrete implementation of :pyclass:`IAudioService` wrapping the existing
helpers in ``src.audio.audio_processing``.
"""

from pathlib import Path

from src.audio.audio_processing import (
    convert_to_wav as _convert_to_wav,
    format_transcript_with_confidence as _fmt_conf,
    format_elapsed_time as _fmt_elapsed,
)

from ..interfaces.audio_service import IAudioService


class AudioService(IAudioService):  # noqa: D401
    """Adapter around the legacy *audio_processing* helpers."""

    # ------------------------------------------------------------------
    def convert_to_wav(self, in_path: str | Path) -> Path:  # noqa: D401
        return Path(_convert_to_wav(in_path))

    # ------------------------------------------------------------------
    def format_transcript_with_confidence(  # noqa: D401
        self, text: str, *, partial: str = "", words_info: list | None = None
    ) -> str:
        return _fmt_conf(text, partial=partial, words_info=words_info)

    # ------------------------------------------------------------------
    def format_elapsed_time(self, start_time: float, current_time: float | None = None) -> str:  # noqa: D401
        return _fmt_elapsed(start_time, current_time) 
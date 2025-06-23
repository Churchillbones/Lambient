from __future__ import annotations

"""Shared audio helper utilities.

This module re-exports commonly used helpers from *audio_processing* to
provide a stable import location for refactored code while we gradually
migrate away from the original implementation.
"""

from .audio_processing import (
    convert_to_wav,
    format_transcript_with_confidence,
    format_elapsed_time,
)

__all__ = [
    "convert_to_wav",
    "format_transcript_with_confidence",
    "format_elapsed_time",
] 
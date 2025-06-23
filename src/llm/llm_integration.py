#!/usr/bin/env python3
from __future__ import annotations

"""DEPRECATED legacy façade for LLM helpers.

The actual implementations now live in:
    • src.llm.routing.generate_note_router
    • src.llm.workflows.traditional (clean_transcription, generate_note, etc.)

This wrapper remains only to keep older import paths working while emitting a
DeprecationWarning.  It should be removed in the next major release.
"""

import warnings
from typing import Any, Dict, Tuple, Optional

from .routing import generate_note_router as _router
from .services import (
    TranscriptionCleanerService,
    SpeakerDiarizerService,
    NoteGeneratorService,
)

warnings.warn(
    "`src.llm.llm_integration` is deprecated; import from the specific submodules instead.",
    DeprecationWarning,
    stacklevel=2,
)

# ---------------------------------------------------------------------------
# Public re-exports matching the original names/signatures
# ---------------------------------------------------------------------------

generate_note_router = _router  # type: ignore[assignment]

# Instantiate services
_cleaner_service = TranscriptionCleanerService()
_diarizer_service = SpeakerDiarizerService()
_note_service = NoteGeneratorService()

async def clean_transcription(*args, **kwargs):  # type: ignore[return-value]
    """Backward-compat async wrapper."""
    return await _cleaner_service(*args, **kwargs)

async def generate_note(*args, **kwargs):  # type: ignore[return-value]
    return await _note_service.generate(*args, **kwargs)

def apply_speaker_diarization(transcript: str) -> str:  # noqa: D401
    return _diarizer_service.tag.__func__.__globals__["_naive"](transcript)  # type: ignore[attr-defined]

async def generate_gpt_speaker_tags(*args, **kwargs):  # type: ignore[return-value]
    return await _diarizer_service.tag(*args, **kwargs)

generate_gpt_speaker_tags.__signature__ = _diarizer_service.tag.__signature__  # type: ignore[attr-defined]

__all__ = [
    "generate_note_router",
    "clean_transcription",
    "generate_note",
    "apply_speaker_diarization",
    "generate_gpt_speaker_tags",
]

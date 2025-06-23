from __future__ import annotations

"""Traditional (non-agent) note-generation workflow and helpers."""

import logging
from typing import Optional, Dict, Any

from ..services import (
    TranscriptionCleanerService,
    SpeakerDiarizerService,
    NoteGeneratorService,
)

# Instantiate service singletons
_cleaner = TranscriptionCleanerService()
_diarizer = SpeakerDiarizerService()
_note_gen = NoteGeneratorService()

# Shared logger
logger = logging.getLogger("ambient_scribe")

# ------------------------------------------------------------------
# Transcription cleanup
# ------------------------------------------------------------------

async def clean_transcription(
    transcript: str,
    api_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    azure_api_version: Optional[str] = None,
    azure_model_name: Optional[str] = None,
    use_local: bool = False,
    local_model: str = "",
    highlight_terms: bool = True,
) -> str:
    """Delegate to :pyclass:`TranscriptionCleanerService`."""
    return await _cleaner(
        transcript,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        azure_api_version=azure_api_version,
        azure_model_name=azure_model_name,
        use_local=use_local,
        local_model=local_model,
        highlight_terms=highlight_terms,
    )

# ------------------------------------------------------------------
# Speaker diarisation helpers
# ------------------------------------------------------------------

def apply_speaker_diarization(transcript: str) -> str:  # noqa: D401
    """Sync helper using naive algorithm in service for backward compat."""
    # Use internal naive logic from SpeakerDiarizerService
    return _diarizer.tag.__func__.__globals__["_naive"](transcript)  # type: ignore[attr-defined]

async def generate_gpt_speaker_tags(
    transcript: str,
    api_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    azure_api_version: Optional[str] = None,
    azure_model_name: Optional[str] = None,
) -> str:  # noqa: D401
    """Delegate to :pyclass:`SpeakerDiarizerService`."""
    return await _diarizer.tag(
        transcript,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        azure_api_version=azure_api_version,
        azure_model_name=azure_model_name,
    )

# ------------------------------------------------------------------
# Note generation (traditional path)
# ------------------------------------------------------------------

async def generate_note(
    transcript: str,
    api_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    azure_api_version: Optional[str] = None,
    azure_model_name: Optional[str] = None,
    prompt_template: str = "",
    use_local: bool = False,
    local_model: str = "",
    patient_data: Optional[Dict] = None,
) -> str:  # noqa: D401
    """Delegate to :pyclass:`NoteGeneratorService`."""
    return await _note_gen.generate(
        transcript=transcript,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        azure_api_version=azure_api_version,
        azure_model_name=azure_model_name,
        prompt_template=prompt_template,
        use_local=use_local,
        local_model=local_model,
        patient_data=patient_data,
    )

__all__ = [
    "clean_transcription",
    "generate_note",
    "apply_speaker_diarization",
    "generate_gpt_speaker_tags",
] 
from __future__ import annotations

from .base import Agent


class TranscriptionCleaner(Agent):
    name = "transcription_cleaner"

    @property
    def system_prompt(self) -> str:  # noqa: D401
        return (
            "You are a medical transcription specialist with expertise in:\n"
            "- Correcting medical terminology and drug names\n"
            "- Identifying and labeling speakers (Doctor, Patient, Nurse)\n"
            "- Fixing grammar while preserving clinical meaning\n"
            "- Expanding medical abbreviations appropriately\n\n"
            "Clean the transcription while maintaining complete accuracy of clinical information.\n"
            "Format with clear speaker labels and paragraph breaks."
        ) 
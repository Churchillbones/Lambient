from __future__ import annotations

"""Agent sub-package for LLM multi-agent pipeline (Phase 3).

Each agent encapsulates a domain-specific prompt and invocation logic.
"""

from .base import Agent  # noqa: F401
from .transcription_cleaner import TranscriptionCleaner  # noqa: F401
from .medical_extractor import MedicalExtractor  # noqa: F401
from .clinical_writer import ClinicalWriter  # noqa: F401
from .quality_reviewer import QualityReviewer  # noqa: F401

__all__ = [
    "Agent",
    "TranscriptionCleaner",
    "MedicalExtractor",
    "ClinicalWriter",
    "QualityReviewer",
] 
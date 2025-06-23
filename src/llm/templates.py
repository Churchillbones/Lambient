"""Template library and helpers for LLM note generation."""
from __future__ import annotations
from typing import Dict

# ------------------------------------------------------------------
# Built-in prompt templates keyed by simple names sent from frontend
# ------------------------------------------------------------------
TEMPLATE_LIBRARY: Dict[str, str] = {
    "SOAP": (
        "You are a clinical documentation assistant. Using the provided encounter transcription, "
        "generate a SOAP note in HTML with <h4> section headings for Subjective, Objective, Assessment, and Plan.\n\n"
        "TRANSCRIPTION:\n{transcription}"
    ),
    "PrimaryCare": (
        "Create a comprehensive primary-care visit note (CC, HPI, ROS, PE, Assessment, Plan) in HTML using the encounter transcription below.\n\n"
        "{transcription}"
    ),
    "Psychiatric Assessment": (
        "Generate a psychiatric assessment (Chief Complaint, History of Present Illness, Mental Status Exam, Risk, Plan) from the transcription.\n\n{transcription}"
    ),
    "Discharge Summary": (
        "Draft a hospital discharge summary (Admission Dx, Hospital Course, Discharge Medications, Follow-up) using the encounter transcription.\n\n{transcription}"
    ),
    "Operative Note": (
        "Produce an operative note (Indication, Procedure Details, Findings, Complications, Disposition) from the following transcription.\n\n{transcription}"
    ),
    "Biopsychosocial": (
        "Create a biopsychosocial assessment note based on the transcription.\n\n{transcription}"
    ),
    "Consultation Note": (
        "Write a specialist consultation note (Reason, Findings, Impression, Recommendations) from the transcription.\n\n{transcription}"
    ),
    "Well-Child Visit": (
        "Generate a well-child visit note (Growth, Development, Exam, Anticipatory Guidance, Plan) using the transcription.\n\n{transcription}"
    ),
    "Emergency Department": (
        "Create an emergency department note (HPI, ROS, PE, ED Course, MDM, Disposition) from this transcription.\n\n{transcription}"
    ),
    "Progress Note": (
        "Craft a follow-up progress note (Interval History, Exam, Assessment, Plan) from the transcription.\n\n{transcription}"
    ),
}


def resolve_template(key_or_prompt: str) -> str:
    """Return full prompt text for a given key or raw prompt string."""
    return TEMPLATE_LIBRARY.get(key_or_prompt, key_or_prompt)

__all__ = ["TEMPLATE_LIBRARY", "resolve_template"] 
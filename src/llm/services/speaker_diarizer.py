from __future__ import annotations

import logging
from typing import Optional

from src.utils import sanitize_input
from ..provider_utils import build_provider

logger = logging.getLogger("ambient_scribe")


def _naive(transcript: str) -> str:  # noqa: D401
    lines = transcript.split("\n")
    out = []
    speaker = 1
    for i, line in enumerate(lines):
        text = line.strip()
        if not text:
            continue
        if i and lines[i - 1].strip():
            speaker = 2 if speaker == 1 else 1
        out.append(f"Speaker {speaker}: {text}")
    return "\n".join(out) if out else f"Speaker 1: {transcript}"


class SpeakerDiarizerService:  # noqa: D401
    """Assign speaker labels using GPT when credentials provided."""

    async def tag(
        self,
        transcript: str,
        *,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        azure_api_version: Optional[str] = None,
        azure_model_name: Optional[str] = None,
    ) -> str:  # noqa: D401
        if not transcript:
            return "ERROR: No transcript provided."

        sanitized = sanitize_input(transcript)
        if not sanitized:
            return _naive(transcript)

        if not all((api_key, azure_endpoint, azure_api_version, azure_model_name)):
            return _naive(transcript)

        provider = build_provider(
            use_local=False,
            api_key=api_key,
            endpoint=azure_endpoint,
            model_name=azure_model_name,
            api_version=azure_api_version,
        )
        prompt = (
            "Analyze the following medical conversation transcript and identify the speakers "
            "(e.g., 'User', 'Patient', 'Nurse'). Prefix each utterance with the identified speaker label "
            "followed by a colon. Maintain the original transcript content accurately.\n\nTRANSCRIPT:\n"
            f"{sanitized}"
        )
        try:
            tagged = await provider.generate_completion(prompt)
            return tagged.strip() if tagged else _naive(transcript)
        except Exception as exc:
            logger.error(f"GPT speaker tagging failed: {exc}")
            return _naive(transcript) 
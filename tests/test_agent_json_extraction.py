from __future__ import annotations

import asyncio
import json

import pytest

from src.llm.llm_agent_enhanced import MedicalNoteAgentPipeline, SpecializedAgent
from core.interfaces.llm_service import ILLMProvider


class DummyProvider(ILLMProvider):
    """A minimal provider that returns a predefined response."""

    def __init__(self, response: str):
        self._response = response

    async def generate_completion(self, prompt: str, **kwargs):  # type: ignore[override]
        return self._response

    async def generate_note(self, transcript: str, **kwargs):  # type: ignore[override]
        return self._response


@pytest.mark.asyncio
async def test_json_extraction_from_code_block():
    """_call_agent should extract JSON wrapped in ```json code fences."""
    payload = {"foo": "bar"}
    markdown_response = f"```json\n{json.dumps(payload)}\n```"

    pipeline = MedicalNoteAgentPipeline(DummyProvider(markdown_response), model_name="mock")
    extracted = await pipeline._call_agent(  # pylint: disable=protected-access
        SpecializedAgent.MEDICAL_EXTRACTOR,
        "ignored",
        is_json_output_expected=True,
    )
    assert json.loads(extracted) == payload


@pytest.mark.asyncio
async def test_completeness_score_below_full():
    """Completeness score should be < 100 when required sections missing."""
    # Missing many required fields – only three provided.
    extractor_output = {
        "Chief Complaint": "Cough",
        "Medications": [],
        "Allergies": "None",
    }
    provider = DummyProvider(json.dumps(extractor_output))
    pipeline = MedicalNoteAgentPipeline(provider, model_name="mock")

    result = await pipeline.extract_medical_information("dummy transcript")
    score = result["_metadata"]["completeness_score"]
    assert score < 100 
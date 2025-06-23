from src.llm.agents import (
    TranscriptionCleaner,
    MedicalExtractor,
    ClinicalWriter,
    QualityReviewer,
)

from core.interfaces.llm_service import ILLMProvider
import asyncio


class MockProvider(ILLMProvider):
    async def generate_completion(self, prompt: str, **kwargs):  # type: ignore[override]
        return "MOCK_OUTPUT"

    async def generate_note(self, transcript: str, **kwargs):  # type: ignore[override]
        return "MOCK_NOTE"


async def _call(agent_cls):
    provider = MockProvider()
    agent = agent_cls(provider)
    result = await agent("Test input")
    assert result == "MOCK_OUTPUT"


def test_transcription_cleaner():
    asyncio.run(_call(TranscriptionCleaner))


def test_medical_extractor():
    asyncio.run(_call(MedicalExtractor))


def test_clinical_writer():
    asyncio.run(_call(ClinicalWriter))


def test_quality_reviewer():
    asyncio.run(_call(QualityReviewer)) 
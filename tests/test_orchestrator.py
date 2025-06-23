from __future__ import annotations

import asyncio
import pytest

from src.llm.pipeline import Orchestrator
from core.interfaces.llm_service import ILLMProvider


class DummyProvider(ILLMProvider):
    async def generate_completion(self, prompt: str, **kwargs):  # type: ignore[override]
        # Simple heuristic to reply differently to expect_json
        if kwargs.get("is_json_output_expected") or kwargs.get("expect_json"):
            return "{}"  # empty JSON object
        return "NOTE_DRAFT"

    async def generate_note(self, transcript: str, **kwargs):  # type: ignore[override]
        return "NOTE"  # not used


async def _run_pipeline():
    orchestrator = Orchestrator(DummyProvider(), include_review=False)
    note, meta = await orchestrator.run("dummy transcript")
    assert note == "NOTE_DRAFT"
    assert any(stage["name"] == "clean" for stage in meta["stages"])


def test_orchestrator_runs():
    asyncio.run(_run_pipeline())


@pytest.mark.anyio
async def test_orchestrator_happy_path(dummy_provider):
    orch = Orchestrator(dummy_provider, include_review=False)
    note, meta = await orch.run("raw transcript text")
    assert "ECHO" in note  # dummy provider echoes prompt
    assert meta["stages"][0]["name"] == "clean"
    # Ensure provider was called at least 3 times (clean, extract, write)
    assert len(dummy_provider.calls) >= 3 
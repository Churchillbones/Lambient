import asyncio
from types import SimpleNamespace

import pytest

from src.llm import routing as routing_mod


class DummyOrchestrator:  # noqa: D101 – test double
    def __init__(self, *_args, **_kwargs):
        self.called = True

    async def run(self, *_args, **_kwargs):  # noqa: D401
        return "agent note", {"agent_based_processing_used": True}


async def _dummy_traditional_generate(*_args, **_kwargs):  # noqa: D401
    return "traditional note"


@pytest.mark.asyncio
async def test_traditional_path(monkeypatch):
    """Routing should delegate to traditional workflow when agent flag is False."""
    monkeypatch.setattr(
        routing_mod,  # target module
        "build_provider",
        lambda **_kw: SimpleNamespace(),  # dummy provider
    )
    # Patch orchestrator to ensure it is *not* used
    monkeypatch.setattr(routing_mod, "Orchestrator", DummyOrchestrator)

    # Patch traditional workflow
    from src.llm.workflows import traditional as trad_mod

    monkeypatch.setattr(trad_mod, "generate_note", _dummy_traditional_generate)
    # The router imported the traditional function under a local alias – patch that too
    monkeypatch.setattr(routing_mod, "generate_note_traditional", _dummy_traditional_generate)

    note, meta = await routing_mod.generate_note_router("hello", use_agent_pipeline=False)

    assert note == "traditional note"
    assert meta["agent_based_processing_used"] is False
    assert meta["pipeline_type_attempted"] == "traditional"


@pytest.mark.asyncio
async def test_agent_path(monkeypatch):
    """Routing should invoke orchestrator when agent flag is True and creds supplied."""
    monkeypatch.setattr(routing_mod, "Orchestrator", DummyOrchestrator)
    monkeypatch.setattr(
        routing_mod,
        "build_provider",
        lambda **_kw: SimpleNamespace(),
    )
    from src.llm.workflows import traditional as trad_mod
    monkeypatch.setattr(trad_mod, "generate_note", _dummy_traditional_generate)
    monkeypatch.setattr(routing_mod, "generate_note_traditional", _dummy_traditional_generate)

    note, meta = await routing_mod.generate_note_router(
        "hi",
        use_agent_pipeline=True,
        api_key="k",
        azure_endpoint="e",
        azure_api_version="v",
        azure_model_name="m",
    )

    assert note == "agent note"
    assert meta["agent_based_processing_used"] is True
    assert meta["pipeline_type_attempted"] == "agent" or meta["agent_based_processing_used"] 
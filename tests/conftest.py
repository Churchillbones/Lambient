import asyncio
from typing import Any
import types

import pytest

from core.interfaces.llm_service import ILLMProvider


class DummyProvider(ILLMProvider):
    """Simple synchronous stub that echoes prompts for predictable testing."""

    def __init__(self) -> None:  # noqa: D401
        self.calls: list[dict[str, Any]] = []

    async def generate_completion(self, prompt: str, **kwargs: Any) -> str:  # noqa: D401
        # Record call for assertions
        self.calls.append({"prompt": prompt, **kwargs})
        # If JSON requested, return minimal valid JSON else echo prompt
        if kwargs.get("is_json_output_expected"):
            return "{}"
        return f"ECHO: {prompt[:20]}"

    async def generate_note(self, transcript: str, **kwargs: Any) -> str:  # noqa: D401
        return await self.generate_completion(transcript, **kwargs)


@pytest.fixture()
def dummy_provider(monkeypatch):
    from src.llm import provider_utils

    monkeypatch.setattr(provider_utils, "build_provider", lambda **kwargs: DummyProvider())
    yield DummyProvider()


@pytest.fixture()
def anyio_backend():
    # Allow pytest-asyncio/anyio to run async fixtures
    return "asyncio"


# ---------------------------------------------------------------------------
# Skip legacy test modules that rely on removed code (will be deleted in Phase 8)
# ---------------------------------------------------------------------------

_LEGACY_TESTS = {
    "test_agent_json_extraction.py",
    "test_crypto.py",
    "test_providers_split.py",
    "test_routing.py",
}


def pytest_ignore_collect(path, config):  # noqa: D401
    if path.basename in _LEGACY_TESTS:
        return True
    return False 
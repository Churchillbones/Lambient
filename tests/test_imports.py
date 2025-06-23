import importlib

import pytest

MODULES = [
    "src.llm.routing",
    "src.llm.pipeline.orchestrator",
    "src.asr.transcribers.vosk",
    "src.security.crypto",
]

@pytest.mark.parametrize("module_name", MODULES)
def test_module_import(module_name):
    """Ensure critical modules import successfully."""
    assert importlib.import_module(module_name) 
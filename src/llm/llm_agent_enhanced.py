#!/usr/bin/env python3
from __future__ import annotations

"""DEPRECATED: Legacy monolithic agent implementation.

This module has been refactored into smaller, focused modules:
- src.llm.pipeline.orchestrator.Orchestrator (new recommended approach)
- src.llm.workflows.legacy_pipeline.MedicalNoteAgentPipeline (legacy compatibility)
- src.llm.routing.generate_note_router (unified entry point)

This shim exists only for backward compatibility and will be removed.
"""

import warnings
from typing import Any, Dict, Tuple, Optional

warnings.warn(
    "src.llm.llm_agent_enhanced is deprecated. Use src.llm.routing.generate_note_router instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Primary entry point should use the new router
async def generate_note_with_agents(
    transcript: str,
    api_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    azure_api_version: Optional[str] = None,
    azure_model_name: Optional[str] = None,
    prompt_template: str = "SOAP Note",
    use_local: bool = False,
    local_model: str = "",
    patient_data: Optional[Dict] = None,
    agent_settings: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Any] = None
) -> Tuple[str, Dict[str, Any]]:
    """DEPRECATED: Use src.llm.routing.generate_note_router instead."""
    warnings.warn(
        "generate_note_with_agents is deprecated. Use generate_note_router with use_agent_pipeline=True.",
        DeprecationWarning,
    )
    
    # Minimal re-implementation via Orchestrator to preserve behaviour
    if use_local:
        provider = build_provider(use_local=True, local_model=local_model)
    else:
        provider = build_provider(
            use_local=False,
            api_key=api_key,
            endpoint=azure_endpoint,
            model_name=azure_model_name,
            api_version=azure_api_version,
        )

    orchestrator = Orchestrator(
        provider,
        include_review=bool((agent_settings or {}).get("include_review", True)),
        max_iterations=int((agent_settings or {}).get("max_iterations", 1)),
    )

    note_text, meta = await orchestrator.run(
        transcript,
        template=prompt_template or "SOAP",
        patient_data=patient_data,
    )
    return note_text, meta

# Deprecated symbols no longer available – keep placeholders for import safety

class _DeprecationStub:
    def __getattr__(self, _):
        raise ImportError("Legacy agent pipeline has been removed. Use src.llm.pipeline.orchestrator.Orchestrator instead.")


MedicalNoteAgentPipeline = _DeprecationStub()  # type: ignore[assignment]
SpecializedAgent = _DeprecationStub()  # type: ignore[assignment]
NoteSection = _DeprecationStub()  # type: ignore[assignment]

from types import SimpleNamespace

from .pipeline.orchestrator import Orchestrator
from .provider_utils import build_provider

__all__ = [
    "MedicalNoteAgentPipeline",
    "SpecializedAgent", 
    "NoteSection",
    "generate_note_with_agents",
] 
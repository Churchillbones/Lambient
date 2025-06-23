from __future__ import annotations

"""High-level router that delegates note-generation requests to either the
agent workflow or the traditional workflow.
"""
import logging
from typing import Dict, Any, Optional, Tuple

from .pipeline import Orchestrator
from .provider_utils import build_provider
from .services import NoteGeneratorService

logger = logging.getLogger("ambient_scribe")

# Service instance for non-agent generation fallback
_note_service = NoteGeneratorService()


async def generate_note_router(
    transcript: str,
    api_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    azure_api_version: Optional[str] = None,
    azure_model_name: Optional[str] = None,
    prompt_template: str = "",
    use_local: bool = False,
    local_model: str = "",
    patient_data: Optional[Dict] = None,
    use_agent_pipeline: bool = False,
    agent_settings: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Any] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Route a request to the agent pipeline or traditional workflow."""
    logger.info("generate_note_router called. use_agent_pipeline=%s, use_local=%s", use_agent_pipeline, use_local)

    metadata: Dict[str, Any] = {
        "pipeline_type_attempted": "agent" if use_agent_pipeline else "traditional",
        "agent_based_processing_used": False,
        "fallback_triggered": False,
        "fallback_reason": None,
    }

    # ------------------------------------------------------------------
    # Agent pipeline path (supports both Azure and local models)
    # ------------------------------------------------------------------
    if use_agent_pipeline:
        if use_local:
            if not local_model:
                metadata["fallback_triggered"] = True
                metadata["fallback_reason"] = "Missing local model name for agent pipeline."
            else:
                try:
                    provider = build_provider(
                        use_local=True,
                        local_model=local_model,
                    )
                except Exception as exc:
                    logger.error("Local agent pipeline provider creation failed: %s", exc, exc_info=True)
                    metadata["fallback_triggered"] = True
                    metadata["fallback_reason"] = f"Local provider error: {exc}"
                    provider = None
        else:
            if not all([api_key, azure_endpoint, azure_api_version, azure_model_name]):
                metadata["fallback_triggered"] = True
                metadata["fallback_reason"] = "Missing Azure credentials or model name for agent pipeline."
                provider = None
            else:
                try:
                    provider = build_provider(
                        use_local=False,
                        api_key=api_key,
                        endpoint=azure_endpoint,
                        model_name=azure_model_name,
                        api_version=azure_api_version,
                    )
                except Exception as exc:
                    logger.error("Azure agent pipeline provider creation failed: %s", exc, exc_info=True)
                    metadata["fallback_triggered"] = True
                    metadata["fallback_reason"] = f"Azure provider error: {exc}"
                    provider = None

        if provider and not metadata["fallback_triggered"]:
            try:

                include_review = bool((agent_settings or {}).get("include_review", True))
                max_iterations = int((agent_settings or {}).get("max_iterations", 1))

                orchestrator = Orchestrator(
                    provider,
                    include_review=include_review,
                    max_iterations=max_iterations,
                )

                note_text, agent_meta = await orchestrator.run(
                    transcript,
                    template=prompt_template or "SOAP",
                    patient_data=patient_data,
                )

                metadata.update(agent_meta)
                metadata["agent_based_processing_used"] = True
                return note_text, metadata
            except Exception as exc:
                logger.error("Agent pipeline failed: %s", exc, exc_info=True)
                metadata["fallback_triggered"] = True
                metadata["fallback_reason"] = f"Agent pipeline error: {exc}"

    # ------------------------------------------------------------------
    # Traditional fallback / primary path
    # ------------------------------------------------------------------
    note_text = await _note_service.generate(
        transcript=transcript,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        azure_api_version=azure_api_version,
        azure_model_name=azure_model_name,
        prompt_template=prompt_template,
        use_local=use_local,
        local_model=local_model,
        patient_data=patient_data,
    )

    metadata["agent_based_processing_used"] = False
    metadata["traditional_note_details"] = {"note_length": len(note_text)}
    metadata["pipeline_type_attempted"] = "traditional"
    return note_text, metadata

__all__ = ["generate_note_router"] 
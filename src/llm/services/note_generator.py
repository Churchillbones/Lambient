from typing import Optional, Dict, Any

import asyncio
import logging

from src.utils import sanitize_input

from ..provider_utils import build_provider
from ..templates import resolve_template
from .token_manager import TokenManager

from ...core.container import global_container
from ...core.interfaces.config_service import IConfigurationService

logger = logging.getLogger("ambient_scribe")


class NoteGeneratorService:  # noqa: D401 – cohesive logic extracted from traditional workflow
    def __init__(self) -> None:
        try:
            self._cfg: IConfigurationService | None = global_container.resolve(IConfigurationService)
        except Exception:
            self._cfg = None

    # ------------------------------------------------------------------
    async def generate(
        self,
        transcript: str,
        *,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        azure_api_version: Optional[str] = None,
        azure_model_name: Optional[str] = None,
        prompt_template: str = "",
        use_local: bool = False,
        local_model: str = "",
        patient_data: Optional[Dict[str, Any]] = None,
    ) -> str:  # noqa: D401
        if not transcript:
            return "Error: No transcript provided for note generation."

        sanitized_transcript = sanitize_input(transcript)
        if not sanitized_transcript:
            return "Error: Transcript content is invalid."

        # Provider (Azure / local Ollama, etc.)
        provider = None
        try:
            provider = build_provider(
                use_local=use_local,
                api_key=api_key,
                endpoint=azure_endpoint,
                model_name=azure_model_name,
                api_version=azure_api_version,
                local_model=local_model,
            )
        except Exception as exc:
            logger.debug(f"Provider construction failed: {exc}")

        # Resolve prompt template
        final_prompt_template = resolve_template(
            prompt_template or "Create a clinical note from the following transcription."
        )

        # Embed patient info
        patient_lines: list[str] = []
        if patient_data:
            if patient_data.get("name"):
                patient_lines.append(f"Name: {sanitize_input(patient_data['name'])}")
            if patient_data.get("ehr_data"):
                patient_lines.append(f"\nEHR DATA:\n{sanitize_input(patient_data['ehr_data'])}")
        patient_info = "\n".join(patient_lines)

        # Build final prompt
        if "{transcription}" in final_prompt_template:
            prompt_body = final_prompt_template.replace("{transcription}", sanitized_transcript)
        else:
            prompt_body = f"{final_prompt_template}\n\n{sanitized_transcript}"

        prompt = f"{prompt_body}\n\nPATIENT INFORMATION:\n{patient_info}" if patient_info else prompt_body

        # Preferred path – provider
        if provider is not None:
            try:
                return await provider.generate_completion(prompt)
            except Exception as exc:
                logger.error(f"Provider generation failed: {exc}")

        # Azure-only long transcript handling
        if not use_local and all((api_key, azure_endpoint, azure_api_version, azure_model_name)):
            tokens = TokenManager.count(sanitized_transcript, "gpt-4o")
            if tokens > 2500:
                approach = self._cfg.get("token_management_approach", "chunking") if self._cfg else "chunking"
                if approach == "chunking":
                    return await asyncio.to_thread(
                        lambda: TokenManager.build_note_chunked(
                            transcript=sanitized_transcript,
                            prompt_template=final_prompt_template,
                            azure_endpoint=azure_endpoint,
                            azure_api_key=api_key,
                            deployment_name=azure_model_name,
                            api_version=azure_api_version,
                            model="gpt-4o",
                        )
                    )
                return await asyncio.to_thread(
                    lambda: TokenManager.build_note_two_stage(
                        transcript=sanitized_transcript,
                        prompt_template=final_prompt_template,
                        azure_endpoint=azure_endpoint,
                        azure_api_key=api_key,
                        deployment_name=azure_model_name,
                        api_version=azure_api_version,
                        model="gpt-4o",
                    )
                )

        return "Error generating note: Provider unavailable or configuration incomplete." 
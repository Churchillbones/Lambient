from __future__ import annotations

import asyncio
from typing import Any

import requests
import logging

from ..exceptions import ConfigurationError
from ..interfaces.llm_service import ILLMProvider
from ..container import global_container
from ..interfaces.config_service import IConfigurationService

__all__ = ["LocalLLMProvider"]


class LocalLLMProvider(ILLMProvider):
    """Generic HTTP provider hitting a configurable local LLM endpoint."""

    def __init__(self, *, endpoint: str | None = None, model: str | None = None) -> None:
        cfg_service = None
        try:
            cfg_service = global_container.resolve(IConfigurationService)
        except Exception:
            pass
        self._endpoint = (endpoint or (cfg_service.get("local_model_api_url") if cfg_service else None)) or "http://localhost:8001/generate_note"
        self._model = model or "gemma3-4b"

    # ------------------------------------------------------------------
    async def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        """Generate a completion using the local LLM."""
        # DEBUG: Log what we're receiving
        logger = logging.getLogger("ambient_scribe")
        logger.info(f"DEBUG: kwargs received = {kwargs}")
        logger.info(f"DEBUG: system_prompt value = {repr(kwargs.get('system_prompt'))}")
        
        payload = {
            "prompt": prompt,
            "model": self._model,
            "system_prompt": kwargs.get("system_prompt"),
            "is_json_output": kwargs.get("is_json_output_expected", False)
        }
        # The endpoint might need to be adjusted based on the task (e.g., cleanup vs. generate)
        # For now, we assume a single versatile endpoint can handle it.
        endpoint_map = {
            "transcription_cleaner": "/cleanup",
            # Other agents can map to different endpoints if needed
        }
        
        # This is a bit of a hack. A better way would be to pass agent type.
        # Checking for keywords in system prompt to guess the endpoint.
        system_prompt_lower = (kwargs.get("system_prompt") or "").lower()
        if "clean" in system_prompt_lower and "transcription" in system_prompt_lower:
             # Assumes the base URL is something like http://localhost:8001
            base_url = self._endpoint.rsplit('/', 1)[0]
            target_endpoint = base_url + "/cleanup_transcription"
        else:
            target_endpoint = self._endpoint # Default to note generation

        final_payload = {k: v for k, v in payload.items() if v is not None}
        return await _post_json(target_endpoint, final_payload)

    async def generate_note(self, transcript: str, **kwargs: Any) -> str:  # noqa: D401
        template = kwargs.get('template', 'Create a clinical note from the following transcription.')
        if "{transcription}" in template:
            prompt = template.format(transcription=transcript)
        else:
            prompt = f"{template}\n\n{transcript}"
        return await self.generate_completion(prompt, **kwargs)


async def _post_json(url: str, payload: dict[str, Any]) -> str:
    logger = logging.getLogger("ambient_scribe")
    
    def _post() -> str:
        logger.info(f"LocalLLMProvider making POST request to {url} with payload keys: {list(payload.keys())}")
        resp = requests.post(url, json=payload, timeout=120)
        logger.info(f"LocalLLMProvider got response: {resp.status_code}")
        if resp.status_code != 200:
            logger.error(f"LocalLLMProvider request failed {resp.status_code}: {resp.text[:200]}")
            raise ConfigurationError(f"Local LLM request failed {resp.status_code}: {resp.text[:200]}")
        
        data = resp.json()
        # Handle different possible response keys from the bridge
        result = data.get("note") or data.get("response") or data.get("cleaned_text") or ""

        logger.info(f"LocalLLMProvider returning result of length: {len(result)}")
        return result

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _post) 
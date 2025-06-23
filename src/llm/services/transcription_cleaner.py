from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import requests

from src.utils import sanitize_input
from ..provider_utils import build_provider
from ...core.container import global_container
from ...core.interfaces.config_service import IConfigurationService

logger = logging.getLogger("ambient_scribe")


class TranscriptionCleanerService:  # noqa: D401
    """Clean raw ASR output for spelling, grammar, and medical terminology."""

    def __init__(self) -> None:
        try:
            self._cfg: IConfigurationService | None = global_container.resolve(IConfigurationService)
        except Exception:
            self._cfg = None

    # ------------------------------------------------------------------
    async def __call__(
        self,
        transcript: str,
        *,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        azure_api_version: Optional[str] = None,
        azure_model_name: Optional[str] = None,
        use_local: bool = False,
        local_model: str = "",
        highlight_terms: bool = True,
        **_: Any,
    ) -> str:  # noqa: D401
        """Return a cleaned transcription string."""
        sanitized = sanitize_input(transcript)
        if not sanitized:
            logger.warning("Transcript became empty after sanitization in cleaner.")
            return "ERROR: Transcript content is invalid."

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

        prompt_parts = [
            "Clean up this medical transcription by:",
            "1. Fixing spelling and grammar errors",
            "2. Correcting medical terminology",
            "3. Improving punctuation and formatting",
        ]
        if highlight_terms:
            prompt_parts.append("4. Highlighting important medical terms with **asterisks** around them")

        prompt = "\n".join(prompt_parts) + "\n\nORIGINAL TRANSCRIPTION:\n" + sanitized

        # Fast path – provider based
        if provider is not None:
            try:
                return await provider.generate_completion(prompt)
            except Exception as exc:
                logger.error(f"Provider cleanup failed, falling back: {exc}")

        # Local LLM fallback via simple HTTP bridge
        if use_local:
            local_url = self._cfg.get("local_model_api_url", "http://localhost:8001/generate_note") if self._cfg else "http://localhost:8001/generate_note"
            try:
                request_payload: dict[str, Any] = {"prompt": prompt}
                if local_model:
                    request_payload["model"] = local_model
                resp = await asyncio.to_thread(lambda: requests.post(local_url, json=request_payload, timeout=30))
                resp.raise_for_status()
                return resp.json().get("cleaned_text", sanitized)
            except Exception as exc:
                logger.error(f"Local LLM cleanup failed: {exc}")

        return sanitized 
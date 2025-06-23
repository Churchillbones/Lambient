from __future__ import annotations

"""Azure OpenAI Whisper transcriber extracted from legacy azure.py."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..base import Transcriber
from ...core.container import global_container
from ...core.interfaces.config_service import IConfigurationService

logger = logging.getLogger("ambient_scribe")

try:
    _cfg: IConfigurationService | None = global_container.resolve(IConfigurationService)
except Exception:
    _cfg = None

def _cfg_get(key: str, default=None):  # noqa: D401
    return _cfg.get(key, default) if _cfg else default


@dataclass
class AzureWhisperTranscriber(Transcriber):
    """Transcriber calling an Azure OpenAI Whisper deployment via SDK."""

    api_key: str
    endpoint: str
    language: str = "en-US"

    def __post_init__(self) -> None:  # noqa: D401
        self.language = self.language or "en-US"

    # ------------------------------------------------------------------
    async def transcribe(self, audio_path: Path, **kwargs) -> str:  # noqa: D401
        if not self.api_key or not self.endpoint:
            return (
                "ERROR: Azure Whisper (OpenAI SDK) requires 'openai_key' and 'openai_endpoint' "
                "for Azure OpenAI service."
            )
        try:
            from openai import AzureOpenAI  # type: ignore
        except Exception:  # pragma: no cover – openai not installed
            return "ERROR: OpenAI SDK not installed."
        try:
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version=str(_cfg_get("api_version", "2024-02-15-preview")),
                azure_endpoint=self.endpoint,
            )
            with open(audio_path, "rb") as fh:
                resp = client.audio.transcriptions.create(
                    model=str(_cfg_get("azure_whisper_deployment_name", "whisper-1")),
                    file=fh,
                    response_format="text",
                    language=self.language.split("-")[0] if self.language else "en",
                )
            return str(resp).strip()
        except Exception as exc:  # pragma: no cover – API failure
            logger.error("Azure Whisper (OpenAI SDK) error: %s", exc)
            return f"ERROR: Azure Whisper (OpenAI SDK) failed: {exc}"


__all__ = ["AzureWhisperTranscriber"] 
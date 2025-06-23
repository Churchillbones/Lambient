from __future__ import annotations

"""Azure Speech transcriber (REST) extracted from legacy azure.py during Phase-6."""

import io
import wave
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from ..base import Transcriber
from ...core.container import global_container
from ...core.interfaces.config_service import IConfigurationService
from ...core.factories.llm_factory import LLMProviderFactory

logger = logging.getLogger("ambient_scribe")

try:
    _cfg: IConfigurationService | None = global_container.resolve(IConfigurationService)
except Exception:
    _cfg = None

def _cfg_get(key: str, default=None):  # noqa: D401
    return _cfg.get(key, default) if _cfg else default


@dataclass
class AzureSpeechTranscriber(Transcriber):
    """Transcriber using Azure Speech service with optional OpenAI post-processing."""

    speech_key: str
    speech_endpoint: str
    openai_key: Optional[str] = None
    openai_endpoint: Optional[str] = None
    language: str = "en-US"
    return_raw: bool = False

    def __post_init__(self) -> None:  # noqa: D401
        self.language = self.language or "en-US"

    # ------------------------------------------------------------------
    def _get_provider(self):  # noqa: D401
        try:
            factory = global_container.resolve(LLMProviderFactory)
        except Exception:
            factory = LLMProviderFactory()
        return factory.create(
            "azure_openai",
            api_key=self.openai_key,
            endpoint=self.openai_endpoint,
            model_name=str(_cfg_get("model_name", "gpt-4o")),
            api_version=str(_cfg_get("api_version", "2024-02-15-preview")),
        )

    # ------------------------------------------------------------------
    def _post_process(self, transcript: str) -> str:
        if (
            not self.openai_key
            or not self.openai_endpoint
            or _cfg_get("skip_openai_summarization", False)
        ):
            return transcript
        try:
            provider = self._get_provider()
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to create provider for post-processing: %s", exc)
            return transcript
        try:
            system_prompt = (
                "Refine this raw audio transcript for clarity and medical context. "
                "If it seems like a summary already, return it as is or improve its structure slightly."
            )
            prompt = f"{system_prompt}\n\nTRANSCRIPT:\n{transcript}"
            refined = asyncio.run(provider.generate_completion(prompt))
            return refined.strip()
        except Exception as exc:  # pragma: no cover
            logger.error("Azure OpenAI post-processing error: %s", exc)
            return transcript

    # ------------------------------------------------------------------
    async def transcribe(self, audio_path: Path, **kwargs) -> str:  # noqa: D401
        if not self.speech_key or not self.speech_endpoint:
            return "ERROR: Azure Speech requires API key and endpoint for transcription."
        try:
            transcript_parts: list[str] = []
            with wave.open(str(audio_path), "rb") as wf:
                channels, sampwidth, framerate, nframes = (
                    wf.getnchannels(),
                    wf.getsampwidth(),
                    wf.getframerate(),
                    wf.getnframes(),
                )
                max_chunk_s = 45
                frames_per_chunk = int(framerate * max_chunk_s)
                num_chunks = (nframes + frames_per_chunk - 1) // frames_per_chunk
                for i in range(num_chunks):
                    wf.setpos(i * frames_per_chunk)
                    chunk_frames = wf.readframes(frames_per_chunk)
                    if not chunk_frames:
                        continue
                    with io.BytesIO() as chunk_io, wave.open(chunk_io, "wb") as chunk_w:
                        chunk_w.setnchannels(channels)
                        chunk_w.setsampwidth(sampwidth)
                        chunk_w.setframerate(framerate)
                        chunk_w.writeframes(chunk_frames)
                        chunk_data = chunk_io.getvalue()
                    url = f"{self.speech_endpoint.rstrip('/')}" \
                          "/speech/recognition/conversation/cognitiveservices/v1"
                    headers = {"api-key": self.speech_key, "Content-Type": "audio/wav"}
                    params = {"language": self.language}
                    resp = requests.post(url, headers=headers, params=params, data=chunk_data, timeout=60)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        if res_json.get("RecognitionStatus") == "Success":
                            text = res_json.get("DisplayText", "").strip()
                            if text:
                                transcript_parts.append(text)
                    else:
                        err_text = (
                            f"Azure Speech API error (Chunk {i+1}): {resp.status_code} - {resp.text[:200]}"
                        )
                        logger.error(err_text)
                        if "language" in resp.text.lower():
                            return f"ERROR: Invalid language '{self.language}' for Azure Speech."
                        return err_text
            combined_transcript = " ".join(transcript_parts).strip()
            if not combined_transcript:
                return "NOTE: Azure Speech generated empty transcript."
            if self.return_raw:
                return combined_transcript
            return self._post_process(combined_transcript)
        except Exception as exc:  # pragma: no cover
            logger.error("Azure Speech pipeline error: %s", exc)
            return f"ERROR: Azure Speech pipeline failed: {exc}"


__all__ = ["AzureSpeechTranscriber"] 
"""Unified entry point for ASR transcribers."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from core.bootstrap import container  # DI bootstrap
from core.factories.transcriber_factory import TranscriberFactory
from .model_spec import ModelSpec, parse_model_spec
from .exceptions import TranscriptionError


async def transcribe_audio(
    audio_path: Union[str, Path],
    model: Union[str, ModelSpec],
    *,
    model_path: Optional[str] = None,
    azure_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    openai_key: Optional[str] = None,
    openai_endpoint: Optional[str] = None,
    language: Optional[str] = "en-US",
    return_raw: bool = False,
) -> str:
    """Dispatch transcription to the requested backend.

    ``model`` may be either the legacy string (e.g. ``"whisper_tiny"``)
    coming from the front-end or the new :class:`ModelSpec` object. The helper
    :func:`parse_model_spec` is used to normalise the value.
    """

    wav_file = Path(audio_path)
    if not wav_file.exists():
        raise TranscriptionError(f"Audio file not found: {audio_path}")

    # ------------------------------------------------------------------
    # Normalise model specification
    # ------------------------------------------------------------------
    spec: ModelSpec = parse_model_spec(model, model_path) if isinstance(model, str) else model

    provider_type, options = spec.to_factory_args()

    factory = container.resolve(TranscriberFactory)

    try:
        transcriber = factory.create(provider_type, **options)  # type: ignore[arg-type]
    except Exception as exc:  # pragma: no cover – factory mis-config
        raise TranscriptionError(str(exc)) from exc

    transcript = await transcriber.transcribe(wav_file)

    # Legacy providers may return error strings – normalise them
    if isinstance(transcript, str) and transcript.startswith("ERROR"):
        raise TranscriptionError(transcript.removeprefix("ERROR:").strip())

    return transcript

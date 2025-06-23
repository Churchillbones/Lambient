from __future__ import annotations

"""Factory for streaming handler implementations (Phase-5)."""

from typing import Any, Dict, Type

from ..exceptions import ConfigurationError, ServiceNotFoundError
from src.asr.streaming.handlers import (
    VoskStreamingHandler,
    WhisperStreamingHandler,
    AzureSpeechStreamingHandler,
)

_HandlerType = Type

__all__ = ["StreamingHandlerFactory"]


class StreamingHandlerFactory:  # noqa: D401
    """Instantiate concrete streaming handler classes by key."""

    _providers: Dict[str, _HandlerType] = {
        "vosk": VoskStreamingHandler,
        "whisper": WhisperStreamingHandler,
        "azure_speech": AzureSpeechStreamingHandler,
    }

    # ------------------------------------------------------------------
    @classmethod
    def create(cls, provider_type: str, **kwargs: Any):  # noqa: D401
        key = provider_type.lower()
        if key not in cls._providers:
            raise ServiceNotFoundError(
                f"Streaming provider '{provider_type}' not supported."
            )
        handler_cls = cls._providers[key]

        # Provider-specific defaults
        if key == "whisper":
            kwargs = {"model_size": kwargs.get("model_size", "tiny"), **kwargs}

        try:
            return handler_cls(**kwargs)
        except TypeError as exc:
            raise ConfigurationError(
                f"Invalid arguments for streaming provider '{provider_type}': {exc}"
            ) from exc

    # ------------------------------------------------------------------
    @classmethod
    def register_provider(cls, key: str, impl: _HandlerType) -> None:  # noqa: D401
        if key in cls._providers:
            raise ConfigurationError(f"Provider '{key}' already registered")
        cls._providers[key] = impl 
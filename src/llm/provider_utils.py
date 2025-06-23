from __future__ import annotations

"""Utility helpers for constructing LLM providers in a single place."""
from typing import Any
from core.bootstrap import container
from core.factories.llm_factory import LLMProviderFactory


def build_provider(
    *,
    use_local: bool,
    api_key: str | None = None,
    endpoint: str | None = None,
    model_name: str | None = None,
    api_version: str | None = None,
    local_model: str = "",
) -> Any:
    """Return an LLM provider instance based on the chosen path."""
    provider_type = "local" if use_local else "azure_openai"
    kwargs: dict[str, Any]
    if use_local:
        kwargs = {"model": local_model} if local_model else {}
    else:
        kwargs = {
            "api_key": api_key,
            "endpoint": endpoint,
            "model_name": model_name,
            "api_version": api_version,
        }
    return container.resolve(LLMProviderFactory).create(provider_type, **kwargs)

__all__ = ["build_provider"] 
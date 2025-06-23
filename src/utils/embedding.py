from __future__ import annotations

import logging
from typing import Optional

from ..core.container import global_container  # type: ignore
from ..core.interfaces.config_service import IConfigurationService  # type: ignore
from ..llm.embedding_service import EmbeddingService

logger = logging.getLogger("ambient_scribe")


def get_embedding_service(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    api_version: str = "2025-01-01-preview",
    verify_ssl: bool = False,
) -> EmbeddingService | None:
    """Return a configured `EmbeddingService` or *None* if configuration missing."""
    try:
        cfg = global_container.resolve(IConfigurationService)
    except Exception:
        cfg = None

    api_key = api_key or (cfg.get("azure.api_key", "") if cfg else "")
    endpoint = endpoint or (cfg.get("azure_embedding_endpoint", "") if cfg else "")

    if not endpoint:
        logger.error("No embedding endpoint configured – cannot create EmbeddingService")
        return None
    return EmbeddingService(api_key, endpoint, api_version, verify_ssl) 
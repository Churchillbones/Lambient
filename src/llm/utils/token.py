from __future__ import annotations

"""Token helpers exposed at `llm.utils.token`.

This module provides thin, synchronous wrappers around the
`ITokenService` registered in the DI container.  Keeping this logic in
one place allows us to swap the underlying implementation (e.g.
`tiktoken` vs. alternative encodings) without touching higher-level
LLM workflows.
"""

from typing import List

from core.container import global_container
from core.interfaces.token_service import ITokenService
import core.services.token_service  # noqa: F401 – ensure service registration side-effect

# Resolve the singleton token service once – faster subsequent calls
_token_service: ITokenService = global_container.resolve(ITokenService)

__all__ = [
    "count",
    "chunk",
]


def count(text: str, model: str = "gpt-4o") -> int:  # noqa: D401
    """Return the number of tokens in *text* for *model* encoding."""

    return _token_service.count(text, model)


def chunk(
    transcript: str,
    max_chunk_tokens: int = 2048,
    model: str = "gpt-4o",
) -> List[str]:  # noqa: D401
    """Split *transcript* into chunks each at most *max_chunk_tokens* long."""

    return _token_service.chunk(transcript, max_chunk_tokens, model) 
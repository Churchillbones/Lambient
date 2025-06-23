from __future__ import annotations

"""Aggregated utility functions.

Phase-6 refactor split the former monolithic utils module into focused
sub-modules.  Public names are re-exported here for backward compatibility so
imports such as ``from src.utils import monitor_resources`` continue to work.
"""

from importlib import import_module
import sys
import warnings

from .audio import get_audio_config, audio_stream  # noqa: F401
from .resource import monitor_resources  # noqa: F401
from .file import get_file_hash  # noqa: F401
from .text import (
    sanitize_input,
    semantic_chunking,
    find_similar_chunks,
    cluster_by_topic,
)  # noqa: F401
from .embedding import get_embedding_service  # noqa: F401

__all__ = [
    "get_audio_config",
    "audio_stream",
    "monitor_resources",
    "get_file_hash",
    "sanitize_input",
    "semantic_chunking",
    "find_similar_chunks",
    "cluster_by_topic",
    "get_embedding_service",
]

# ---------------------------------------------------------------------------
# Deprecation notice
# ---------------------------------------------------------------------------
warnings.filterwarnings("default", category=DeprecationWarning)
warnings.warn(
    "Direct access to 'src.utils' is deprecated; import from dedicated sub-modules "
    "such as 'src.utils.text' instead.",
    DeprecationWarning,
    stacklevel=2,
)

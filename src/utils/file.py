from __future__ import annotations

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger("ambient_scribe")


def get_file_hash(file_path: str | Path) -> str:
    """Return SHA-256 hex digest for *file_path* or empty string on errors."""
    path = Path(file_path)
    if not path.exists():
        logger.error("File not found for hashing: %s", file_path)
        return ""
    sha256 = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()
    except Exception as exc:  # pragma: no cover
        logger.error("Error hashing file %s: %s", file_path, exc)
        return "" 
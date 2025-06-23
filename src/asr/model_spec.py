from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

__all__ = ["ModelSpec", "parse_model_spec"]


@dataclass(slots=True)
class ModelSpec:
    """Normalized description of the requested ASR backend/model."""

    engine: Literal["vosk", "whisper", "azure_speech"]
    size: Optional[str] = None  # Whisper size, etc.
    model_path: Optional[Path] = None  # Used by Vosk if provided

    def to_factory_args(self) -> tuple[str, dict]:  # noqa: D401
        """Return provider_type string and kwargs for *TranscriberFactory* usage."""
        if self.engine == "vosk":
            return "vosk", {"model_path": str(self.model_path) if self.model_path else None}
        if self.engine == "whisper":
            return "whisper", {"size": self.size or "tiny"}
        if self.engine == "azure_speech":
            return "azure_speech", {}
        raise ValueError(f"Unsupported engine: {self.engine}")


def parse_model_spec(model_str: str, model_path: str | None = None) -> ModelSpec:  # noqa: D401
    """Convert legacy *model* query parameters into a :class:`ModelSpec`."""
    model_str = model_str.strip().lower()

    if model_str.startswith("whisper:"):
        _engine, _size = model_str.split(":", 1)
        return ModelSpec(engine="whisper", size=_size)
    if model_str.startswith("whisper_"):
        _engine, _size = model_str.split("_", 1)
        return ModelSpec(engine="whisper", size=_size)
    if model_str == "whisper":
        return ModelSpec(engine="whisper", size="tiny")

    if model_str.startswith("vosk"):
        # Handles "vosk" and "vosk_model"
        return ModelSpec(engine="vosk", model_path=Path(model_path) if model_path else None)

    if model_str in {"azure", "azure_speech", "azure-whisper"}:
        return ModelSpec(engine="azure_speech")

    # Fallback to whisper tiny to avoid breaking existing flows
    return ModelSpec(engine="whisper", size="tiny") 
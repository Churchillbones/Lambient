from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict

__all__ = ["ApplicationSettings", "AzureSettings"]


class AzureSettings(BaseSettings):
    """Azure OpenAI/Speech configuration settings."""

    api_key: Optional[str] = Field(None, env="AZURE_API_KEY")
    endpoint: Optional[str] = Field(None, env="AZURE_ENDPOINT")
    model_name: str = Field("gpt-4o", env="MODEL_NAME")
    api_version: str = Field("2024-02-15-preview", env="API_VERSION")

    speech_api_key: Optional[str] = Field(None, env="AZURE_SPEECH_API_KEY")
    speech_endpoint: Optional[str] = Field(None, env="AZURE_SPEECH_ENDPOINT")

    @field_validator("endpoint", mode="before")
    def _validate_endpoint(cls, v: Optional[str]) -> Optional[str]:  # noqa: D401
        if v and not v.startswith("https://"):
            raise ValueError("Azure endpoint must start with https://")
        return v

    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


class ApplicationSettings(BaseSettings):
    """Top-level application settings loaded from environment variables."""

    debug_mode: bool = Field(False, env="DEBUG_MODE")
    local_model_api_url: str = Field("http://localhost:8001/generate_note", env="LOCAL_MODEL_API_URL")

    # Nested groups
    azure: AzureSettings = Field(default_factory=AzureSettings)

    # Paths
    base_dir: Path = Field(Path("./app_data"), env="BASE_DIR")

    # Audio / tool paths
    ffmpeg_path: Optional[str] = Field(None, env="FFMPEG_PATH")

    # Whisper related
    whisper_device: str = Field("cpu", env="WHISPER_DEVICE")
    whisper_models_dir: Path = Field(Path("./app_data/whisper_models"), env="WHISPER_MODELS_DIR")

    # Feature toggles & misc
    skip_openai_summarization: bool = Field(False, env="SKIP_OPENAI_SUMMARIZATION")
    token_management_approach: str = Field("chunking", env="TOKEN_MANAGEMENT_APPROACH")
    azure_whisper_deployment_name: str = Field("whisper-1", env="AZURE_WHISPER_DEPLOYMENT_NAME")

    @field_validator("base_dir", mode="before")
    def _ensure_base_dir(cls, v) -> Path:  # noqa: D401
        path = Path(v) if not isinstance(v, Path) else v
        path.mkdir(parents=True, exist_ok=True)
        return path

    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore") 
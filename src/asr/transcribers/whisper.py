from __future__ import annotations

import os
import subprocess
from pathlib import Path
import logging

from ..base import Transcriber
from ...core.container import global_container
from ...core.interfaces.config_service import IConfigurationService

# ------------------------------------------------------------------
# Configuration & logging helpers
# ------------------------------------------------------------------
logger = logging.getLogger("ambient_scribe")

try:
    _cfg: IConfigurationService | None = global_container.resolve(IConfigurationService)
except Exception:
    _cfg = None

def _cfg_get(key: str, default=None):  # noqa: D401
    return _cfg.get(key, default) if _cfg else default


class WhisperTranscriber(Transcriber):
    """Transcriber using local Whisper models."""

    # ------------------------------------------------------------------
    _MODEL_CACHE: dict[str, "whisper.Whisper"] = {}
    _FFMPEG_CHECKED = False
    _FFMPEG_AVAILABLE = False

    _VALID_SIZES = ["tiny", "base", "small", "medium", "large"]

    def __init__(self, size: str = "tiny") -> None:  # noqa: D401
        if size not in self._VALID_SIZES:
            raise ValueError(
                f"Invalid Whisper size '{size}'. Options: {', '.join(self._VALID_SIZES)}"
            )
        self.size = size

    # ------------------------------------------------------------------
    def _verify_ffmpeg(self) -> bool:  # noqa: D401
        # Try multiple FFmpeg locations in order of preference
        ffmpeg_candidates = []
        
        # 1. User-configured path
        cfg_path = _cfg_get("ffmpeg_path", "")
        if cfg_path:
            ffmpeg_candidates.append(Path(cfg_path))
        
        # 2. Project bundled FFmpeg (relative to project root)
        project_root = Path(__file__).parent.parent.parent.parent  # Go up to project root
        bundled_ffmpeg = project_root / "ffmpeg" / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if bundled_ffmpeg.exists():
            ffmpeg_candidates.append(bundled_ffmpeg)
        
        # 3. System PATH
        ffmpeg_candidates.append(Path("ffmpeg.exe" if os.name == "nt" else "ffmpeg"))

        try:
            # Try each candidate
            for ffmpeg_path in ffmpeg_candidates:
                try:
                    if ffmpeg_path.name in ["ffmpeg.exe", "ffmpeg"] and not ffmpeg_path.is_absolute():
                        # For system PATH lookup, use string
                        cmd = [str(ffmpeg_path), "-version"]
                    else:
                        # For absolute paths, verify existence first
                        if not ffmpeg_path.exists():
                            continue
                        cmd = [str(ffmpeg_path.resolve()), "-version"]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    )
                    
                    if result.returncode == 0:
                        logger.info("FFmpeg verified at: %s", ffmpeg_path)
                        return True
                    else:
                        logger.debug("FFmpeg test failed at %s: %s", ffmpeg_path, result.stderr)
                        
                except (subprocess.TimeoutExpired, subprocess.SubprocessError, PermissionError) as exc:
                    logger.debug("FFmpeg verification failed for %s: %s", ffmpeg_path, exc)
                    continue
                    
            # If we get here, none of the candidates worked
            logger.warning("FFmpeg not found in any of the expected locations: %s", 
                          [str(p) for p in ffmpeg_candidates])
            return False
            
        except Exception as exc:
            logger.error("Unexpected error during FFmpeg verification: %s", exc)
            return False

    # ------------------------------------------------------------------
    def _download_model(self, custom_dir: Path) -> None:  # noqa: D401
        import whisper  # type: ignore

        custom_dir.mkdir(parents=True, exist_ok=True)
        device_to_use = str(_cfg_get("whisper_device", "cpu"))
        logger.info("Downloading Whisper model '%s' to %s", self.size, custom_dir)
        try:
            whisper.load_model(self.size, download_root=str(custom_dir), device=device_to_use)
            logger.info("Successfully downloaded Whisper model '%s'", self.size)
        except Exception as exc:
            logger.error("Failed to download Whisper model '%s': %s", self.size, exc)
            raise

    # ------------------------------------------------------------------
    async def transcribe(self, audio_path: Path, **kwargs) -> str:  # noqa: D401
        """Transcribe audio file using local Whisper model."""
        if not WhisperTranscriber._FFMPEG_CHECKED:
            WhisperTranscriber._FFMPEG_CHECKED = True
            WhisperTranscriber._FFMPEG_AVAILABLE = self._verify_ffmpeg()
        
        # FFmpeg is preferred but not strictly required for some audio formats
        if not WhisperTranscriber._FFMPEG_AVAILABLE:
            logger.warning("FFmpeg not available - Whisper will work with limited audio format support")

        import whisper  # type: ignore

        custom_model_dir = Path(str(_cfg_get("whisper_models_dir", Path("./app_data/whisper_models"))))
        custom_model_dir.mkdir(parents=True, exist_ok=True)

        device_to_use = str(_cfg_get("whisper_device", "cpu"))
        try:
            if self.size in WhisperTranscriber._MODEL_CACHE:
                model = WhisperTranscriber._MODEL_CACHE[self.size]
            else:
                logger.info("Loading Whisper model '%s' from %s", self.size, custom_model_dir)
                model = whisper.load_model(
                    name=self.size,
                    download_root=str(custom_model_dir),
                    device=device_to_use,
                )
                WhisperTranscriber._MODEL_CACHE[self.size] = model
        except Exception as exc:  # pragma: no cover – download
            logger.error("Failed to load Whisper model %s: %s", self.size, exc)
            return f"ERROR: Failed to load Whisper model: {exc}"

        try:
            result = model.transcribe(
                str(audio_path),
                language="en",
                fp16=False if device_to_use == "cpu" else True,
            )
            return result.get("text", "").strip()
        except Exception as exc:  # pragma: no cover – runtime
            logger.error("Local Whisper recognition failed (size=%s): %s", self.size, exc)
            return f"ERROR: Local Whisper transcription failed: {exc}"

__all__ = ["WhisperTranscriber"] 
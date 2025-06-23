from __future__ import annotations

import json
import os
import zipfile
import logging
from pathlib import Path
from typing import Optional

import requests
from dataclasses import dataclass

from ..base import Transcriber  # one level up to src.asr.base
from ...core.container import global_container
from ...core.interfaces.config_service import IConfigurationService

logger = logging.getLogger("ambient_scribe")


@dataclass
class VoskTranscriber(Transcriber):
    """Transcriber using the Vosk engine."""

    model_path: Optional[Path] = None

    # ------------------------------------------------------------------
    def __post_init__(self) -> None:  # noqa: D401
        if isinstance(self.model_path, str):
            self.model_path = Path(self.model_path)

        # Resolve application directories via DI when available
        try:
            config_service = global_container.resolve(IConfigurationService)
            base_dir = config_service.get("base_dir", Path("./app_data"))
        except Exception:  # pragma: no cover – container not bootstrapped
            base_dir = Path("./app_data")

        model_dir = base_dir / "models"
        self.model_path = self.model_path or model_dir / "vosk-model-small-en-us-0.15"

    # ------------------------------------------------------------------
    def _download_small_model(self, target_dir: Path) -> None:  # noqa: D401
        model_name = "vosk-model-small-en-us-0.15"
        final_model_path = target_dir / model_name
        if final_model_path.exists() and any(final_model_path.iterdir()):
            return

        url = (
            "https://alphacephei.com/vosk/models/"
            "vosk-model-small-en-us-0.15.zip"
        )
        zip_path = target_dir / f"{model_name}.zip"
        target_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading Vosk model %s to %s", model_name, zip_path)
        with requests.get(url, timeout=120, stream=True) as resp:
            resp.raise_for_status()
            with open(zip_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192 * 16):
                    fh.write(chunk)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(target_dir)
        os.remove(zip_path)
        if not final_model_path.exists():
            raise FileNotFoundError(
                f"Vosk model dir {final_model_path} not found after extraction."
            )

    # ------------------------------------------------------------------
    def _ensure_model(self) -> Optional[str]:  # noqa: D401
        if not self.model_path.exists() or not any(self.model_path.iterdir()):
            logger.warning("Vosk model directory not found or empty: %s", self.model_path)

            try:
                config_service = global_container.resolve(IConfigurationService)
                base_dir = config_service.get("base_dir", Path("./app_data"))
            except Exception:
                base_dir = Path("./app_data")

            model_dir = base_dir / "models"
            default_path = model_dir / "vosk-model-small-en-us-0.15"

            if self.model_path == default_path:
                try:
                    self._download_small_model(model_dir)
                except Exception as exc:  # pragma: no cover – network failure
                    logger.error("Failed to download default Vosk model: %s", exc)
                    return f"ERROR: Failed to download default Vosk model: {exc}"
                if not self.model_path.exists() or not any(self.model_path.iterdir()):
                    return (
                        "ERROR: Default Vosk model download attempted but failed at "
                        f"{self.model_path}"
                    )
            else:
                return f"ERROR: Vosk model not found at {self.model_path}."
        return None

    # ------------------------------------------------------------------
    async def transcribe(self, audio_path: Path, **kwargs) -> str:  # noqa: D401
        try:
            from vosk import Model, KaldiRecognizer  # type: ignore
        except ImportError:
            return (
                "ERROR: 'vosk' library not installed. "
                "Please install it (e.g., pip install vosk)."
            )

        # Ensure WAV format
        try:
            from ...audio.utils import convert_to_wav  # use new audio utils path

            logger.info("Converting audio file: %s", audio_path)
            converted_path = convert_to_wav(audio_path)
            audio_path = Path(converted_path)
            logger.info("Audio converted to: %s", audio_path)
        except Exception as exc:
            logger.error("Audio conversion failed, using original file: %s", exc)

        err = self._ensure_model()
        if err:
            logger.error("Model validation failed: %s", err)
            return err

        try:
            logger.info("Loading Vosk model from: %s", self.model_path)
            model = Model(str(self.model_path))

            # Obtain sample rate from config
            sample_rate = 16000
            try:
                config_service = global_container.resolve(IConfigurationService)
                sample_rate = config_service.get("rate", 16000)
            except Exception:
                pass

            logger.info("Using sample rate: %s", sample_rate)
            rec = KaldiRecognizer(model, sample_rate)
            rec.SetWords(True)

            import wave  # stdlib

            logger.info("Opening WAV file: %s", audio_path)
            with wave.open(str(audio_path), "rb") as wf:
                channels = wf.getnchannels()
                rate = wf.getframerate()
                frames = wf.getnframes()
                logger.info("WAV format: %s ch, %s Hz, %s frames", channels, rate, frames)

                if channels != 1:
                    logger.warning("Audio has %s channels, expected 1 (mono)", channels)
                if rate != sample_rate:
                    logger.warning("Audio sample rate is %s, expected %s", rate, sample_rate)

                total_frames_processed = 0
                while True:
                    audio_frames = wf.readframes(4000)
                    if not audio_frames:
                        break
                    rec.AcceptWaveform(audio_frames)
                    total_frames_processed += len(audio_frames)

                logger.info("Processed %s audio bytes", total_frames_processed)

            logger.info("Retrieving final result from Vosk …")
            final_result = json.loads(rec.FinalResult())
            transcript = final_result.get("text", "").strip()
            logger.info("Vosk transcription result length=%s", len(transcript))
            return transcript

        except Exception as exc:  # pragma: no cover – runtime failure
            logger.error("Vosk recognition failed (model: %s): %s", self.model_path, exc)
            return f"ERROR: Vosk transcription failed: {exc}"

__all__ = ["VoskTranscriber"] 
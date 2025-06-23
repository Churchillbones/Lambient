from __future__ import annotations

import queue
import time
from dataclasses import dataclass, field
from typing import List

from src.utils.audio import get_audio_config
import logging

logger = logging.getLogger("ambient_scribe")


@dataclass
class WhisperStreamingHandler:
    model_size: str
    update_queue: queue.Queue
    model: object = field(init=False)
    buf: List[bytes] = field(default_factory=list)
    last_time: float = field(default_factory=time.time)
    start_time: float = field(default_factory=time.time)
    current_transcription: str = ""
    processing_interval: float = 1.5
    window_duration: float = 6.0

    def __post_init__(self) -> None:
        import whisper  # type: ignore

        self.model = whisper.load_model(self.model_size)

    # ------------------------------------------------------------------
    def __call__(self, chunk: bytes) -> None:
        import numpy as np  # type: ignore

        self.buf.append(chunk)
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        if time.time() - self.last_time < self.processing_interval:
            audio_cfg = get_audio_config()
            total_bytes = sum(len(c) for c in self.buf)
            audio_seconds = total_bytes / (audio_cfg["rate"] * 2)
            partial_text = (
                f"[Processing {audio_seconds:.1f}s of audio...]" if audio_seconds > 1.0 else ("..." if self.current_transcription else "")
            )
            self.update_queue.put(
                {
                    "type": "partial",
                    "text": self.current_transcription,
                    "words_info": [],
                    "is_final": False,
                    "elapsed": elapsed_str,
                    "partial": partial_text,
                    "processing": False,
                }
            )
            return

        self.last_time = time.time()
        self.update_queue.put(
            {
                "type": "partial",
                "text": self.current_transcription,
                "words_info": [],
                "is_final": False,
                "elapsed": elapsed_str,
                "partial": "Processing audio...",
                "processing": True,
            }
        )

        audio_buffer = b"".join(self.buf)
        audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
        try:
            result = self.model.transcribe(audio_np, language="en", fp16=False, suppress_tokens=None)
            txt = result.get("text", "").strip()
            if txt:
                self.current_transcription = txt
                self.update_queue.put({"type": "final", "text": txt})
        except Exception as exc:  # pragma: no cover
            logger.error("Whisper transcription error: %s", exc)
            self.update_queue.put(
                {
                    "type": "partial",
                    "text": self.current_transcription,
                    "words_info": [],
                    "is_final": False,
                    "elapsed": elapsed_str,
                    "partial": f"Whisper Error: {str(exc)[:50]}...",
                }
            )

        audio_cfg = get_audio_config()
        max_buf_bytes = int(self.window_duration * audio_cfg["rate"] * 2)
        if len(audio_buffer) > max_buf_bytes:
            start_byte = len(audio_buffer) - max_buf_bytes
            new_buf = audio_buffer[start_byte:]
            chunk_sz = audio_cfg["chunk"] * 2
            self.buf = [new_buf[i : i + chunk_sz] for i in range(0, len(new_buf), chunk_sz)] 
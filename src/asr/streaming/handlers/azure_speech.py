from __future__ import annotations

import io
import queue
import time
import wave
from dataclasses import dataclass, field
from typing import List

from src.utils.audio import get_audio_config
import logging

logger = logging.getLogger("ambient_scribe")


@dataclass
class AzureSpeechStreamingHandler:
    api_key: str
    endpoint: str
    update_queue: queue.Queue
    buf: List[bytes] = field(default_factory=list)
    last_time: float = field(default_factory=time.time)
    start_time: float = field(default_factory=time.time)
    chunk_duration: int = 45
    full_transcription: str = ""

    # ------------------------------------------------------------------
    def __call__(self, chunk: bytes) -> None:
        import requests  # type: ignore

        self.buf.append(chunk)
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        audio_buffer = b"".join(self.buf)
        audio_cfg = get_audio_config()
        samples_per_chunk = int(audio_cfg["rate"] * self.chunk_duration)
        audio_samples = len(audio_buffer) // 2

        if not (
            audio_samples >= samples_per_chunk or time.time() - self.last_time >= 3
        ):
            return

        self.last_time = time.time()
        self.update_queue.put(
            {
                "text": self.full_transcription,
                "words_info": [],
                "is_final": False,
                "elapsed": elapsed_str,
                "partial": "Processing audio...",
                "processing": True,
            }
        )

        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(audio_cfg["channels"])
                wf.setsampwidth(2)
                wf.setframerate(audio_cfg["rate"])
                wf.writeframes(audio_buffer)

            url = f"{self.endpoint.rstrip('/')}/speech/recognition/conversation/cognitiveservices/v1"
            headers = {"api-key": self.api_key, "Content-Type": "audio/wav"}
            params = {"language": "en-US"}
            resp = requests.post(url, headers=headers, params=params, data=wav_buffer.getvalue())
            if resp.status_code == 200:
                result = resp.json()
                if result.get("RecognitionStatus") == "Success":
                    text = result.get("DisplayText", "").strip()
                    if text:
                        self.full_transcription = f"{self.full_transcription} {text}".strip()
                        self.update_queue.put(
                            {
                                "text": self.full_transcription,
                                "words_info": [],
                                "is_final": True,
                                "elapsed": elapsed_str,
                                "partial": "",
                                "processing": False,
                            }
                        )
            else:
                logger.error("Azure Speech API error: %s - %s", resp.status_code, resp.text[:200])
        except Exception as exc:  # pragma: no cover
            logger.error("Azure Speech transcription error: %s", exc)
            self.update_queue.put(
                {
                    "text": self.full_transcription,
                    "words_info": [],
                    "is_final": False,
                    "elapsed": elapsed_str,
                    "partial": f"Azure Error: {str(exc)[:50]}...",
                    "processing": False,
                }
            )

        if audio_samples >= samples_per_chunk:
            excess_samples = audio_samples - samples_per_chunk
            new_buf_bytes = audio_buffer[-excess_samples * 2 :]
            chunk_sz = audio_cfg["chunk"] * 2
            self.buf = [new_buf_bytes[i : i + chunk_sz] for i in range(0, len(new_buf_bytes), chunk_sz)]
        else:
            self.buf = [] 
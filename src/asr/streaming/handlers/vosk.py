from __future__ import annotations

import json
import queue
import time
from dataclasses import dataclass, field
from typing import List

from src.utils.audio import get_audio_config

import logging

logger = logging.getLogger("ambient_scribe")


def _load_vosk_model(model_path: str):  # noqa: D401
    from vosk import Model  # type: ignore

    cache = getattr(_load_vosk_model, "_cache", {})
    if model_path not in cache:
        cache[model_path] = Model(model_path)
        setattr(_load_vosk_model, "_cache", cache)
    return cache[model_path]


@dataclass
class VoskStreamingHandler:  # noqa: D401 – already well-named
    model_path: str
    update_queue: queue.Queue
    rec: object = field(init=False)
    transcriptions: List[str] = field(default_factory=list)
    last_final_text: str = ""
    start_time: float = field(default_factory=time.time)

    def __post_init__(self) -> None:  # noqa: D401
        from vosk import KaldiRecognizer  # type: ignore

        audio_cfg = get_audio_config()
        self.rec = KaldiRecognizer(_load_vosk_model(self.model_path), audio_cfg["rate"])
        self.rec.SetWords(True)

    # ------------------------------------------------------------------
    def __call__(self, chunk: bytes) -> None:  # noqa: D401
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        if self.rec.AcceptWaveform(chunk):
            result = json.loads(self.rec.Result())
            final_text = result.get("text", "").strip()
            words_info = result.get("result", []) if final_text else []
            if final_text and final_text != self.last_final_text:
                self.last_final_text = final_text
                self.transcriptions.append(final_text)
                self.update_queue.put(
                    {
                        "text": " ".join(self.transcriptions),
                        "words_info": words_info,
                        "is_final": True,
                        "elapsed": elapsed_str,
                        "partial": "",
                    }
                )
        else:
            partial_result = json.loads(self.rec.PartialResult())
            partial = partial_result.get("partial", "").strip()
            if partial:
                self.update_queue.put(
                    {
                        "text": " ".join(self.transcriptions),
                        "words_info": [],
                        "is_final": False,
                        "elapsed": elapsed_str,
                        "partial": partial,
                    }
                ) 
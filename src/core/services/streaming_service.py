from __future__ import annotations

"""Centralised session manager for real-time ASR streaming."""

import queue
import threading
import time
import uuid
from typing import Any, Dict, Iterable

from ..interfaces.streaming_service import IStreamingService
from ..factories.streaming_factory import StreamingHandlerFactory
from src.utils import monitor_resources


class StreamingService(IStreamingService):  # noqa: D401
    """Manage multiple concurrent streaming sessions and resource metrics."""

    _CLEANUP_INTERVAL = 10  # seconds between house-keeping runs

    def __init__(self, *, inactivity_timeout: int = 60) -> None:  # noqa: D401
        self._sessions: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._inactivity_timeout = inactivity_timeout
        self._housekeeper = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._housekeeper.start()

    # ------------------------------------------------------------------
    def start_session(self, engine: str, **options: Any) -> str:  # noqa: D401
        session_id = uuid.uuid4().hex
        updates_q: queue.Queue = queue.Queue(maxsize=256)
        handler = StreamingHandlerFactory.create(engine, update_queue=updates_q, **options)
        measure, get_results = monitor_resources()
        self._sessions[session_id] = {
            "handler": handler,
            "queue": updates_q,
            "measure": measure,
            "metrics": get_results,
            "quality_sum": 0.0,
            "quality_count": 0,
            "peak_amplitude": 0.0,
            "last_activity": time.time(),
        }
        return session_id

    # ------------------------------------------------------------------
    def process_chunk(self, session_id: str, chunk: bytes) -> None:  # noqa: D401
        with self._lock:
            sess = self._sessions.get(session_id)
        if not sess:
            raise KeyError(f"Unknown session {session_id}")
        sess["measure"]()
        sess["last_activity"] = time.time()

        # Audio quality assessment – simple RMS amplitude metric
        try:
            import numpy as _np  # local import avoids mandatory dependency

            if chunk:
                audio_arr = _np.frombuffer(chunk, dtype=_np.int16).astype(_np.float32)
                rms = float(_np.mean(_np.abs(audio_arr)) / 32768.0)
                sess["quality_sum"] += rms
                sess["quality_count"] += 1
                if rms > sess["peak_amplitude"]:
                    sess["peak_amplitude"] = rms
        except Exception:
            # Ignore quality calculation errors to avoid disrupting streaming
            pass

        sess["handler"](chunk)  # call the handler

    # ------------------------------------------------------------------
    def get_updates(self, session_id: str) -> Iterable[dict]:  # noqa: D401
        sess = self._sessions.get(session_id)
        if not sess:
            raise KeyError(session_id)
        q: queue.Queue = sess["queue"]
        while not q.empty():
            yield q.get()

    # ------------------------------------------------------------------
    def end_session(self, session_id: str) -> None:  # noqa: D401
        with self._lock:
            sess = self._sessions.pop(session_id, None)
        if not sess:
            return
        # Capture metrics for future reporting if needed
        metrics = sess["metrics"]()
        if sess["quality_count"]:
            metrics["avg_amplitude"] = sess["quality_sum"] / sess["quality_count"]
            metrics["peak_amplitude"] = sess["peak_amplitude"]
        sess["queue"].put({"type": "metrics", **metrics})

    # ------------------------------------------------------------------
    def _cleanup_loop(self) -> None:  # noqa: D401
        """Background thread that disposes inactive sessions."""
        while True:
            time.sleep(self._CLEANUP_INTERVAL)
            now = time.time()
            expired: list[str] = []
            with self._lock:
                for sid, sess in list(self._sessions.items()):
                    if now - sess["last_activity"] > self._inactivity_timeout:
                        expired.append(sid)
                for sid in expired:
                    _sess = self._sessions.pop(sid)
                    # Post final metrics if consumer still reading
                    metrics = _sess["metrics"]()
                    if _sess["quality_count"]:
                        metrics["avg_amplitude"] = _sess["quality_sum"] / _sess["quality_count"]
                        metrics["peak_amplitude"] = _sess["peak_amplitude"]
                    _sess["queue"].put({"type": "metrics", "expired": True, **metrics})
            # Loop continues 
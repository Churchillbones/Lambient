from __future__ import annotations

import logging
import os
from typing import Callable, Tuple

logger = logging.getLogger("ambient_scribe")


def monitor_resources() -> Tuple[Callable[[], None], Callable[[], dict]]:
    """Return (measure, results) callables for lightweight resource tracking."""
    try:
        import psutil  # local import – optional dependency

        process = psutil.Process(os.getpid())
        baseline_mem = process.memory_info().rss / 1024 / 1024  # MB
        measurements: list[tuple[float, float]] = []

        def measure() -> None:
            try:
                cpu = process.cpu_percent(interval=None)
                mem = process.memory_info().rss / 1024 / 1024
                measurements.append((cpu, mem))
            except Exception:  # pragma: no cover
                pass

        def results() -> dict:
            if not measurements:
                return {"cpu_avg": 0.0, "memory_avg": 0.0, "peak_memory": baseline_mem}
            cpus, mems = zip(*measurements)
            return {
                "cpu_avg": sum(cpus) / len(cpus),
                "memory_avg": sum(mems) / len(mems),
                "peak_memory": max(mems),
            }

        return measure, results
    except ImportError:
        logger.debug("psutil not installed – resource monitoring disabled")

    # Fallback no-op functions
    def _noop() -> None:  # noqa: D401
        pass

    def _empty() -> dict:  # noqa: D401
        return {"cpu_avg": 0.0, "memory_avg": 0.0, "peak_memory": 0.0}

    return _noop, _empty 
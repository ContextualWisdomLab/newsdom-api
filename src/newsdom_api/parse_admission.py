"""Process-local, non-waiting admission for expensive `/parse` work."""

from __future__ import annotations

import threading

from .config import MAX_MAX_CONCURRENT_PARSES, MIN_MAX_CONCURRENT_PARSES


class ParseAdmissionLimiter:
    """Bound concurrent MinerU parses on one FastAPI application instance."""

    def __init__(self, capacity: int) -> None:
        """Create a bounded semaphore that refuses to wait or silently expand."""

        if not (MIN_MAX_CONCURRENT_PARSES <= capacity <= MAX_MAX_CONCURRENT_PARSES):
            raise ValueError("capacity must be an integer in 1..128")
        self.capacity = capacity
        self._semaphore = threading.BoundedSemaphore(value=capacity)

    def try_acquire(self) -> bool:
        """Return True when this request may start; False when the replica is full."""

        return self._semaphore.acquire(blocking=False)

    def release(self) -> None:
        """Return one lease. A double release raises instead of adding capacity."""

        self._semaphore.release()

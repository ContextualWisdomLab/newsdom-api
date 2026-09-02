"""Application-local concurrency state for parser work."""

from threading import BoundedSemaphore


class ParseAdmissionLimiter:
    """Bound concurrent parser work without queueing excess requests."""

    __slots__ = ("_capacity", "_semaphore")

    def __init__(self, capacity: int) -> None:
        """Create a limiter with an immutable number of parser leases."""

        self._capacity = capacity
        self._semaphore = BoundedSemaphore(capacity)

    @property
    def capacity(self) -> int:
        """Return the immutable number of parser leases."""

        return self._capacity

    def try_acquire(self) -> bool:
        """Acquire one parser lease immediately or report saturation."""

        return self._semaphore.acquire(blocking=False)

    def release(self) -> None:
        """Return one previously acquired parser lease."""

        self._semaphore.release()

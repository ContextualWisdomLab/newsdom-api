"""Application-local concurrency state for parser work."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParseAdmissionLimiter:
    """Store the immutable parser concurrency budget for one application."""

    capacity: int

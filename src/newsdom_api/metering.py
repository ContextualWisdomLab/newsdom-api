"""Count-only usage export helpers for parsed document results."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .schemas import ParseResponse


_RESERVED_EVENT_FIELDS = frozenset(
    {
        "document_job_reference",
        "document_id",
        "occurred_at",
        "pdf_bytes",
        "page_count",
        "ocr_page_count",
        "extracted_block_count",
        "shard_reference",
        "credential_reference",
        "project_reference",
    }
)


class CanonicalParseUsageSink:
    """Build and enqueue a count-only event for one parse result."""

    def __init__(
        self,
        *,
        event_builder: Callable[..., Mapping[str, Any]],
        enqueue: Callable[[Mapping[str, Any]], None],
        identity: Mapping[str, str | None],
    ) -> None:
        """Store the event builder, durable enqueue callback, and parse identity."""
        reserved = _RESERVED_EVENT_FIELDS.intersection(identity)
        if reserved:
            names = ", ".join(sorted(reserved))
            raise ValueError(f"identity contains reserved event fields: {names}")
        self._event_builder = event_builder
        self._enqueue = enqueue
        self._identity = dict(identity)

    def emit_parse(
        self,
        response: ParseResponse,
        *,
        document_job_reference: str,
        pdf_bytes: bytes | bytearray | memoryview,
        ocr_page_count: int,
        occurred_at: str,
        shard_reference: str | None = None,
        credential_reference: str | None = None,
        project_reference: str | None = None,
    ) -> None:
        """Export parser counts without passing document text to the builder."""
        if response.quality.status not in {"success", "partial"}:
            return
        event = self._event_builder(
            **self._identity,
            document_job_reference=document_job_reference,
            document_id=response.document_id,
            occurred_at=occurred_at,
            pdf_bytes=len(pdf_bytes),
            page_count=len(response.pages),
            ocr_page_count=ocr_page_count,
            extracted_block_count=_extracted_block_count(response),
            shard_reference=shard_reference,
            credential_reference=credential_reference,
            project_reference=project_reference,
        )
        self._enqueue(event)


def _extracted_block_count(response: ParseResponse) -> int:
    """Count extracted text-bearing blocks while retaining no text content."""
    count = 0
    for page in response.pages:
        count += len(page.ads) + len(page.headers) + len(page.footers)
        count += len(page.page_numbers)
        for article in page.articles:
            count += 1
            count += len(article.body_blocks)
            count += len(article.captions) + len(article.footnotes)
            for image in article.images:
                count += len(image.captions) + len(image.footnotes)
    return count


__all__ = ["CanonicalParseUsageSink"]

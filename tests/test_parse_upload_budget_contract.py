"""Exact streaming-boundary regressions for the public PDF upload budget."""

import pytest
from fastapi import HTTPException

from newsdom_api.main import MAX_PARSE_UPLOAD_BYTES, parse


class _VirtualPdfUpload:
    """Stream a bounded synthetic PDF without allocating the full payload."""

    content_type = "application/pdf"
    filename = "fixture.pdf"
    size = None

    def __init__(self, total_bytes: int) -> None:
        self.total_bytes = total_bytes
        self.bytes_returned = 0

    async def read(self, size: int = -1) -> bytes:
        """Return at most ``size`` bytes while preserving a valid PDF prefix."""
        remaining = self.total_bytes - self.bytes_returned
        if remaining <= 0:
            return b""
        count = remaining if size < 0 else min(size, remaining)
        prefix = b"%PDF-"
        start = self.bytes_returned
        chunk = b""
        if start < len(prefix):
            prefix_count = min(count, len(prefix) - start)
            chunk = prefix[start : start + prefix_count]
            count -= prefix_count
        if count:
            chunk += b"x" * count
        self.bytes_returned += len(chunk)
        return chunk


@pytest.mark.asyncio
async def test_streaming_upload_rejects_exact_first_byte_over_budget() -> None:
    """Reject after consuming exactly the first byte beyond the 64 MiB ceiling."""
    upload = _VirtualPdfUpload(MAX_PARSE_UPLOAD_BYTES + 1)

    with pytest.raises(HTTPException) as exc_info:
        await parse(upload)

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "Payload Too Large"
    assert upload.bytes_returned == MAX_PARSE_UPLOAD_BYTES + 1

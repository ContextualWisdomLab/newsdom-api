"""Regression tests for bounded PDF upload read sizes."""

import pytest

from newsdom_api.main import UPLOAD_READ_CHUNK_SIZE_BYTES, parse


class _ReadTrackingUpload:
    """Minimal upload double that records every requested read size."""

    content_type = "application/pdf"
    filename = "fixture.pdf"
    size = None

    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._offset = 0
        self.read_sizes: list[int] = []

    async def read(self, size: int = -1) -> bytes:
        """Return the next payload chunk while recording the requested size."""
        self.read_sizes.append(size)
        if size < 0:
            size = len(self._payload) - self._offset
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


@pytest.mark.asyncio
async def test_parse_uses_configured_upload_chunk_size(monkeypatch) -> None:
    """Read every post-header upload chunk with the configured 1 MiB bound."""
    upload = _ReadTrackingUpload(b"%PDF-" + (b"x" * 7))

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _path: None)
    monkeypatch.setattr(
        "newsdom_api.main.parse_pdf",
        lambda *_args, **_kwargs: {"document_id": "fixture", "pages": []},
    )

    result = await parse(upload)

    assert result == {"document_id": "fixture", "pages": []}
    assert upload.read_sizes == [5, UPLOAD_READ_CHUNK_SIZE_BYTES, UPLOAD_READ_CHUNK_SIZE_BYTES]
    assert UPLOAD_READ_CHUNK_SIZE_BYTES == 1024 * 1024

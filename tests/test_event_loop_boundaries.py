"""Concurrency-boundary tests for synchronous parser validation work."""

from __future__ import annotations

import threading

import pytest

from newsdom_api.main import parse


class _Upload:
    content_type = "application/pdf"
    filename = "fixture.pdf"

    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._offset = 0
        self.size = len(payload)

    async def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self._payload) - self._offset
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


@pytest.mark.asyncio
async def test_parse_offloads_pdf_structure_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_loop_thread = threading.get_ident()
    validation_threads: list[int] = []

    def fake_validate(file_path) -> None:
        assert file_path.read_bytes().startswith(b"%PDF-")
        validation_threads.append(threading.get_ident())

    def fake_parse_pdf(file_path, *, filename: str, **_kwargs):
        assert file_path.exists()
        assert filename == "fixture.pdf"
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", fake_validate)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)

    result = await parse(_Upload(b"%PDF-1.4\n%%EOF\n"))

    assert result == {"document_id": "fixture", "pages": []}
    assert len(validation_threads) == 1
    assert validation_threads[0] != event_loop_thread

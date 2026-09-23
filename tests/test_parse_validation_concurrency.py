import asyncio
import threading
from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from newsdom_api.main import parse
from newsdom_api.schemas import PageNode, ParseQuality, ParseResponse


@pytest.mark.asyncio
async def test_pdf_structure_validation_does_not_block_event_loop(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    validation_timed_out = threading.Event()

    def blocking_validate(_path):
        started.set()
        if not release.wait(timeout=1.0):
            validation_timed_out.set()

    def fake_parse_pdf(_path, filename="upload.pdf", **_kwargs):
        return ParseResponse(
            document_id=filename,
            pages=[
                PageNode(
                    page_number=1,
                    articles=[],
                    ads=[],
                    headers=[],
                )
            ],
            quality=ParseQuality(status="success", parser="mineru"),
        )

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", blocking_validate)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)

    payload = b"%PDF-1.4\n%synthetic\n"
    upload = UploadFile(
        file=BytesIO(payload),
        filename="fixture.pdf",
        size=len(payload),
        headers=Headers({"content-type": "application/pdf"}),
    )

    async def release_from_event_loop():
        while not started.is_set():
            await asyncio.sleep(0)
        release.set()

    releaser = asyncio.create_task(release_from_event_loop())
    try:
        result = await asyncio.wait_for(parse(upload), timeout=3.0)
        await releaser
    finally:
        release.set()
        await upload.close()

    assert result.document_id == "fixture.pdf"
    assert not validation_timed_out.is_set()

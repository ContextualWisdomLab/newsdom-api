import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from newsdom_api.main import MAX_PARSE_UPLOAD_BYTES, app, parse


class _OversizePdfUpload:
    """Model an oversized PDF that must be rejected before any body read."""

    content_type = "application/pdf"
    filename = "oversize.pdf"
    size = MAX_PARSE_UPLOAD_BYTES + 1

    async def read(self, _size: int = -1) -> bytes:
        """Fail the test if the size metadata fast path attempts a body read."""

        raise AssertionError("oversized upload must be rejected before reading bytes")


def test_parse_unsupported_media_guides_the_caller_to_the_next_action() -> None:
    """A 415 response should explain the accepted input and recovery action."""

    response = TestClient(app).post(
        "/parse",
        files={"file": ("fixture.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == (
        "Only structurally valid PDF files are accepted. "
        "Upload a valid PDF and try again."
    )


@pytest.mark.asyncio
async def test_parse_oversize_upload_names_the_binary_limit_and_next_action() -> None:
    """A 413 response should give the exact binary limit without reading the body."""

    with pytest.raises(HTTPException) as exc_info:
        await parse(_OversizePdfUpload())

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == (
        "File exceeds the 20 MiB upload limit. "
        "Choose a smaller PDF and try again."
    )

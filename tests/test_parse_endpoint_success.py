from fastapi.testclient import TestClient

import newsdom_api.main as main_module
from newsdom_api.schemas import PageNode, ParseQuality, ParseResponse


def _successful_parse_response(filename: str) -> ParseResponse:
    """Return the stable synthetic DOM used by parse endpoint boundary tests."""
    return ParseResponse(
        document_id=filename,
        pages=[
            PageNode(
                page_number=1,
                articles=[],
                ads=[],
                headers=["Synthetic Chemical Daily"],
            )
        ],
        quality=ParseQuality(status="success", parser="mineru"),
    )


def test_parse_endpoint_returns_dom(monkeypatch):
    def fake_parse_pdf_bytes(
        data: bytes, filename: str = "upload.pdf", **kwargs
    ) -> ParseResponse:
        return _successful_parse_response(filename)

    monkeypatch.setattr(main_module, "_validate_pdf_structure", lambda _: None)
    monkeypatch.setattr(main_module, "parse_pdf", fake_parse_pdf_bytes)

    client = TestClient(main_module.app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["document_id"] == "fixture.pdf"


def test_parse_endpoint_offloads_pdf_validation_and_parse(monkeypatch):
    """Untrusted PDF parsing work must not execute on the ASGI event-loop thread."""
    offloaded = []

    def fake_validate_pdf_structure(file_path):
        assert file_path.exists()

    def fake_parse_pdf(
        file_path, filename: str = "upload.pdf", **kwargs
    ) -> ParseResponse:
        assert file_path.exists()
        return _successful_parse_response(filename)

    async def record_to_thread(function, *args, **kwargs):
        offloaded.append(function)
        return function(*args, **kwargs)

    monkeypatch.setattr(main_module, "_validate_pdf_structure", fake_validate_pdf_structure)
    monkeypatch.setattr(main_module, "parse_pdf", fake_parse_pdf)
    monkeypatch.setattr(main_module.asyncio, "to_thread", record_to_thread)

    client = TestClient(main_module.app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 200
    assert offloaded == [fake_validate_pdf_structure, fake_parse_pdf]

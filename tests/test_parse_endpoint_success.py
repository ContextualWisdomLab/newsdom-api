from fastapi.testclient import TestClient

from newsdom_api.main import app
from newsdom_api.schemas import PageNode, ParseQuality, ParseResponse


def test_parse_endpoint_returns_dom(monkeypatch):
    def fake_parse_pdf_bytes(
        data: bytes, filename: str = "upload.pdf"
    ) -> ParseResponse:
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

    monkeypatch.setattr("newsdom_api.main.parse_pdf_bytes", fake_parse_pdf_bytes)

    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["document_id"] == "fixture.pdf"

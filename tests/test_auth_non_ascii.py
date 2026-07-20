import pytest
from fastapi.testclient import TestClient
from newsdom_api.config import API_TOKEN_ENV_VAR
from newsdom_api.main import app

_PDF_FILES = {"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")}

@pytest.fixture
def stub_parser(monkeypatch):
    def fake_parse_pdf(file_path, filename, **kwargs):
        return {"document_id": "fixture", "pages": []}
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)

def test_parse_rejects_invalid_bearer_non_ascii_when_secret_set(monkeypatch, stub_parser):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")
    client = TestClient(app)
    # The header must be passed as bytes, otherwise TestClient raises ascii decode error internally before it reaches the endpoint
    # The endpoint parses this into `provided` as a string with unicode chars, which causes hmac.compare_digest to raise a TypeError
    # Because FastAPI raises an exception, the exception_handler handles it and returns a 500
    response = client.post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": b"Bearer \xf0\x9f\x98\x80"}, # Emoji '😀' encoded to utf-8
    )
    assert response.status_code == 401

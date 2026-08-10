from fastapi.testclient import TestClient
from newsdom_api.main import app
from newsdom_api.config import API_TOKEN_ENV_VAR

_PDF_FILES = {"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")}


def test_parse_hmac_unicode_headers(monkeypatch, stub_parser=None):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")
    client = TestClient(app)
    response = client.post(
        "/parse",
        files=_PDF_FILES,
        headers=[(b"Authorization", "Bearer 💩".encode("utf-8"))],
    )
    assert response.status_code == 401

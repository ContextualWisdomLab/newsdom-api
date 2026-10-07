from fastapi.testclient import TestClient
from newsdom_api.config import RuntimeSettings
from newsdom_api.main import create_app
import io

settings = RuntimeSettings(api_token="test_token")
app = create_app(settings=settings)
client = TestClient(app, raise_server_exceptions=False)


def _assert_security_headers(headers):
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert (
        headers.get("Content-Security-Policy")
        == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )
    assert headers.get("Referrer-Policy") == "no-referrer"
    assert headers.get("Cache-Control") == "no-store, no-cache, max-age=0"


def test_404_security_headers():
    response = client.get("/nonexistent-path")
    assert response.status_code == 404
    _assert_security_headers(response.headers)


def test_401_security_headers():
    response = client.post("/parse", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    _assert_security_headers(response.headers)


def test_415_security_headers():
    response = client.post(
        "/parse",
        headers={"Authorization": "Bearer test_token"},
        files={"file": ("fixture.txt", io.BytesIO(b"not a pdf"), "text/plain")},
    )
    assert response.status_code == 415
    _assert_security_headers(response.headers)


def test_422_security_headers():
    response = client.post(
        "/parse",
        headers={"Authorization": "Bearer test_token"},
        files={
            "file": (
                "fixture.pdf",
                io.BytesIO(b"%PDF-1.4\n%synthetic\n"),
                "application/pdf",
            )
        },
        data={"language": "invalid-language-input"},
    )
    assert response.status_code == 422
    _assert_security_headers(response.headers)

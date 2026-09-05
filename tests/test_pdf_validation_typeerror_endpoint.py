from fastapi.testclient import TestClient

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app


def _development_app():
    """Create an explicit auth-disabled app for parser endpoint classification tests."""

    return create_app(
        RuntimeSettings(
            authentication_mode=AuthenticationMode.DISABLED,
            runtime_profile=RuntimeProfile.DEVELOPMENT,
        ),
        runtime_readiness_probe=lambda: True,
    )


def test_parse_endpoint_sanitizes_type_error_as_unsupported_media(monkeypatch):
    """Classify a parser TypeError as invalid PDF input at the public endpoint."""

    def fail_reader(_stream, *, strict):
        assert strict is True
        raise TypeError("malformed dictionary")

    monkeypatch.setattr("newsdom_api.main.PdfReader", fail_reader)

    with TestClient(_development_app()) as client:
        response = client.post(
            "/parse",
            files={"file": ("fixture.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
        )

    assert response.status_code == 415
    assert response.json() == {"detail": "Unsupported Media Type"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"

from fastapi.testclient import TestClient

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app


def _development_app():
    """Create an explicitly auth-disabled development app for parser-boundary tests."""

    return create_app(
        RuntimeSettings(
            authentication_mode=AuthenticationMode.DISABLED,
            runtime_profile=RuntimeProfile.DEVELOPMENT,
        ),
        runtime_readiness_probe=lambda: True,
    )


def test_parse_endpoint_sanitizes_unexpected_parser_fault_as_500(monkeypatch):
    """Keep unexpected parser defects on the sanitized server-fault boundary."""

    def fail_reader(_stream, *, strict):
        assert strict is True
        raise RuntimeError("synthetic parser defect")

    monkeypatch.setattr("newsdom_api.main.PdfReader", fail_reader)

    with TestClient(_development_app(), raise_server_exceptions=False) as client:
        response = client.post(
            "/parse",
            files={"file": ("fixture.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"

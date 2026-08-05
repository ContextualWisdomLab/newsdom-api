"""Fail-closed authentication and readiness regression contracts."""

from __future__ import annotations

from fastapi.testclient import TestClient

from newsdom_api.config import API_TOKEN_ENV_VAR
from newsdom_api.main import app

_PDF_FILES = {
    "file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")
}


def test_default_configuration_without_token_blocks_parser_before_work(
    monkeypatch,
) -> None:
    """Required authentication must not silently become open when its token is absent."""

    monkeypatch.delenv(API_TOKEN_ENV_VAR, raising=False)
    monkeypatch.delenv("NEWSDOM_AUTH_MODE", raising=False)
    monkeypatch.delenv("NEWSDOM_RUNTIME_PROFILE", raising=False)
    parser_called = False

    def fake_parse_pdf(*_args, **_kwargs):
        nonlocal parser_called
        parser_called = True
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)

    response = TestClient(app, raise_server_exceptions=False).post(
        "/parse", files=_PDF_FILES
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}
    assert parser_called is False


def test_ready_fails_closed_when_required_authentication_is_unconfigured(
    monkeypatch,
) -> None:
    """Traffic readiness must expose invalid auth configuration without secret detail."""

    monkeypatch.delenv(API_TOKEN_ENV_VAR, raising=False)
    monkeypatch.delenv("NEWSDOM_AUTH_MODE", raising=False)
    monkeypatch.delenv("NEWSDOM_RUNTIME_PROFILE", raising=False)

    response = TestClient(app, raise_server_exceptions=False).get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}
    assert "token" not in response.text.lower()
    assert "environment" not in response.text.lower()


def test_health_remains_liveness_only_when_authentication_is_unconfigured(
    monkeypatch,
) -> None:
    """Liveness must remain independent from authentication readiness."""

    monkeypatch.delenv(API_TOKEN_ENV_VAR, raising=False)
    monkeypatch.delenv("NEWSDOM_AUTH_MODE", raising=False)
    monkeypatch.delenv("NEWSDOM_RUNTIME_PROFILE", raising=False)

    response = TestClient(app, raise_server_exceptions=False).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

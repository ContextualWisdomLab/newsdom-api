"""Fail-closed authentication and readiness regression contracts."""

from __future__ import annotations

from fastapi.testclient import TestClient

from newsdom_api.config import (
    AuthenticationMode,
    RuntimeProfile,
    RuntimeSettings,
)
from newsdom_api.main import create_app

_PDF_FILES = {
    "file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")
}


def test_default_configuration_without_token_blocks_parser_before_work(
    monkeypatch,
) -> None:
    """Missing required auth must block parsing before downstream work."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token=None,
    )
    parser_called = False

    def fake_parse_pdf(*_args, **_kwargs):
        nonlocal parser_called
        parser_called = True
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)

    application = create_app(
        settings, runtime_readiness_probe=lambda: True
    )
    response = TestClient(
        application, raise_server_exceptions=False
    ).post("/parse", files=_PDF_FILES)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}
    assert parser_called is False


def test_ready_fails_closed_when_required_authentication_is_unconfigured(
    monkeypatch,
) -> None:
    """Readiness must expose invalid auth configuration without secret detail."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token=None,
    )
    application = create_app(
        settings, runtime_readiness_probe=lambda: True
    )

    response = TestClient(
        application, raise_server_exceptions=False
    ).get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}
    assert "token" not in response.text.lower()
    assert "environment" not in response.text.lower()


def test_health_remains_liveness_only_when_authentication_is_unconfigured(
    monkeypatch,
) -> None:
    """Liveness must remain independent from authentication readiness."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token=None,
    )
    application = create_app(
        settings, runtime_readiness_probe=lambda: False
    )

    response = TestClient(
        application, raise_server_exceptions=False
    ).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

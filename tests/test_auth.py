"""Tests for the optional bearer-auth gate on ``/parse`` and the leaf config."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from newsdom_api import config
from newsdom_api.config import API_TOKEN_ENV_VAR, get_api_token
from newsdom_api.main import app

_PDF_FILES = {"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")}


@pytest.fixture
def stub_parser(monkeypatch):
    """Bypass PDF structure validation and MinerU so auth is what is exercised."""

    def fake_parse_pdf(file_path, filename, **kwargs):
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)


def test_parse_is_open_when_no_secret_configured(monkeypatch, stub_parser):
    monkeypatch.delenv(API_TOKEN_ENV_VAR, raising=False)
    client = TestClient(app)
    response = client.post("/parse", files=_PDF_FILES)
    assert response.status_code == 200


def test_parse_requires_bearer_when_secret_set_and_header_missing(
    monkeypatch, stub_parser
):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")
    client = TestClient(app)
    response = client.post("/parse", files=_PDF_FILES)
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_parse_rejects_invalid_bearer_when_secret_set(monkeypatch, stub_parser):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")
    client = TestClient(app)
    response = client.post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_parse_accepts_valid_bearer_when_secret_set(monkeypatch, stub_parser):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")
    client = TestClient(app)
    response = client.post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": "Bearer s3cret-token"},
    )
    assert response.status_code == 200


def test_health_is_unauthenticated_even_when_secret_set(monkeypatch):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_api_token_returns_none_when_unset(monkeypatch):
    monkeypatch.delenv(API_TOKEN_ENV_VAR, raising=False)
    assert get_api_token() is None


def test_get_api_token_treats_blank_as_disabled(monkeypatch):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "   ")
    assert get_api_token() is None


def test_get_api_token_strips_surrounding_whitespace(monkeypatch):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "  padded-token\n")
    assert get_api_token() == "padded-token"


def test_config_module_exposes_env_var_name():
    assert config.API_TOKEN_ENV_VAR == "NEWSDOM_API_TOKEN"


def test_require_authorization_rejects_non_ascii_header_safely(monkeypatch):
    """Ensure non-ASCII characters in the Authorization header are handled safely.
    Python's hmac.compare_digest raises a TypeError if passed strings with
    non-ASCII characters. This test directly invokes the dependency rather than
    using TestClient, as httpx strictly validates header encoding beforehand.
    """
    from newsdom_api.main import require_authorization
    from fastapi import HTTPException

    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")
    with pytest.raises(HTTPException) as exc:
        require_authorization("Bearer 안녕")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Unauthorized"

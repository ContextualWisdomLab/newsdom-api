"""Tests for the fail-closed bearer-auth gate on ``/parse``."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from newsdom_api import config
from newsdom_api.config import (
    ALLOW_ANONYMOUS_ENV_VAR,
    API_TOKEN_ENV_VAR,
    allow_anonymous,
    get_api_token,
)
from newsdom_api.main import app

_PDF_FILES = {"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")}


@pytest.fixture
def stub_parser(monkeypatch):
    """Bypass PDF structure validation and MinerU so auth is what is exercised."""

    def fake_parse_pdf(file_path, filename, **kwargs):
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)


def test_parse_requires_auth_when_no_secret_or_opt_in(monkeypatch, stub_parser):
    monkeypatch.delenv(API_TOKEN_ENV_VAR, raising=False)
    monkeypatch.delenv(ALLOW_ANONYMOUS_ENV_VAR, raising=False)
    client = TestClient(app)
    response = client.post("/parse", files=_PDF_FILES)
    assert response.status_code == 401


def test_parse_is_open_only_with_explicit_anonymous_opt_in(monkeypatch, stub_parser):
    monkeypatch.delenv(API_TOKEN_ENV_VAR, raising=False)
    monkeypatch.setenv(ALLOW_ANONYMOUS_ENV_VAR, "true")
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
    assert config.ALLOW_ANONYMOUS_ENV_VAR == "NEWSDOM_ALLOW_ANONYMOUS"


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_allow_anonymous_accepts_explicit_true_values(monkeypatch, value):
    monkeypatch.setenv(ALLOW_ANONYMOUS_ENV_VAR, value)
    assert allow_anonymous() is True


def test_allow_anonymous_rejects_implicit_or_unknown_values(monkeypatch):
    monkeypatch.setenv(ALLOW_ANONYMOUS_ENV_VAR, "development")
    assert allow_anonymous() is False

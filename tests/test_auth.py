"""Tests for the optional bearer-auth gate on ``/parse`` and the leaf config."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from newsdom_api import config
from newsdom_api.config import API_TOKEN_ENV_VAR, get_api_token
from newsdom_api.main import app, require_authorization

_PDF_FILES = {"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")}
_MAX_AUTHORIZATION_HEADER_BYTES = 8 * 1024


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


def test_require_authorization_rejects_non_ascii_without_type_error(monkeypatch):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")

    with pytest.raises(HTTPException) as exc_info:
        require_authorization("Bearer 잘못된-토큰")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_require_authorization_accepts_matching_non_ascii_secret(monkeypatch):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "비밀-토큰")

    assert require_authorization("Bearer 비밀-토큰") is None


@pytest.mark.parametrize(
    "authorization",
    [
        "Bearer " + ("a" * _MAX_AUTHORIZATION_HEADER_BYTES),
        "Bearer " + ("界" * (_MAX_AUTHORIZATION_HEADER_BYTES // 2)),
    ],
    ids=["oversized-ascii", "oversized-utf8"],
)
def test_require_authorization_rejects_oversized_header_before_digest(
    monkeypatch, authorization
):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")

    def unexpected_digest(*_args, **_kwargs):
        pytest.fail("oversized headers must be rejected before constant-time comparison")

    monkeypatch.setattr("newsdom_api.main.hmac.compare_digest", unexpected_digest)

    with pytest.raises(HTTPException) as exc_info:
        require_authorization(authorization)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


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

"""Tests for the optional bearer-auth gate on ``/parse`` and the leaf config."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from newsdom_api import config
from newsdom_api.config import API_TOKEN_ENV_VAR, get_api_token
from newsdom_api.main import (
    MAX_AUTHORIZATION_HEADER_BYTES,
    _encode_bounded_utf8,
    app,
)

_PDF_FILES = {"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")}
_BEARER_PREFIX = "Bearer "


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


def test_parse_rejects_non_ascii_bearer_when_secret_set(monkeypatch, stub_parser):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")
    client = TestClient(app, raise_server_exceptions=False)
    # ASGI/TestClient raw byte tuples inject non-ASCII header octets without
    # client-side Unicode normalization or validation.
    response = client.post(
        "/parse",
        files=_PDF_FILES,
        headers=[(b"Authorization", b"Bearer \xe2\x98\x83")],
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


def test_parse_accepts_exact_8k_authorization_boundary(monkeypatch, stub_parser):
    token = "a" * (MAX_AUTHORIZATION_HEADER_BYTES - len(_BEARER_PREFIX))
    authorization = f"{_BEARER_PREFIX}{token}"
    assert len(authorization.encode("utf-8")) == MAX_AUTHORIZATION_HEADER_BYTES

    monkeypatch.setenv(API_TOKEN_ENV_VAR, token)
    response = TestClient(app).post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": authorization},
    )

    assert response.status_code == 200


def test_parse_rejects_authorization_over_8k_without_calling_parser(
    monkeypatch, stub_parser
):
    monkeypatch.setenv(API_TOKEN_ENV_VAR, "s3cret-token")
    monkeypatch.setattr(
        "newsdom_api.main.parse_pdf",
        lambda *_args, **_kwargs: pytest.fail("parser must not run after auth failure"),
    )
    authorization = "a" * (MAX_AUTHORIZATION_HEADER_BYTES + 1)

    response = TestClient(app).post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": authorization},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_parse_rejects_configured_token_over_8k(monkeypatch, stub_parser):
    token = "a" * (MAX_AUTHORIZATION_HEADER_BYTES - len(_BEARER_PREFIX) + 1)
    monkeypatch.setenv(API_TOKEN_ENV_VAR, token)

    response = TestClient(app).post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": f"{_BEARER_PREFIX}{token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_bounded_utf8_encoder_accepts_exact_ascii_limit():
    value = "a" * MAX_AUTHORIZATION_HEADER_BYTES
    assert _encode_bounded_utf8(
        value, max_bytes=MAX_AUTHORIZATION_HEADER_BYTES
    ) == value.encode("utf-8")


def test_bounded_utf8_encoder_rejects_codepoint_overflow_before_encoding():
    value = "a" * (MAX_AUTHORIZATION_HEADER_BYTES + 1)
    assert (
        _encode_bounded_utf8(value, max_bytes=MAX_AUTHORIZATION_HEADER_BYTES) is None
    )


def test_bounded_utf8_encoder_rejects_multibyte_overflow():
    value = "é" * ((MAX_AUTHORIZATION_HEADER_BYTES // 2) + 1)
    assert len(value) < MAX_AUTHORIZATION_HEADER_BYTES
    assert len(value.encode("utf-8")) > MAX_AUTHORIZATION_HEADER_BYTES
    assert (
        _encode_bounded_utf8(value, max_bytes=MAX_AUTHORIZATION_HEADER_BYTES) is None
    )


def test_bounded_utf8_encoder_rejects_unpaired_surrogate():
    assert _encode_bounded_utf8("\ud800", max_bytes=8) is None


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

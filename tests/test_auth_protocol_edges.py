"""Protocol and failure-edge tests for fail-closed parser authentication."""

from __future__ import annotations

import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from newsdom_api.config import (
    MAX_BEARER_HEADER_BYTES,
    RuntimeConfigurationError,
    RuntimeSettings,
)
from newsdom_api.main import create_app

_PDF_FILES = {
    "file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")
}
_BEARER_PREFIX = "Bearer "


@pytest.fixture
def parser_spy(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Replace parser work while retaining an exact invocation count."""

    calls = {"count": 0}

    def fake_parse_pdf(*_args, **_kwargs):
        calls["count"] += 1
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)
    return calls


def test_required_mode_accepts_mixed_case_bearer_scheme(
    parser_spy: dict[str, int],
) -> None:
    """HTTP authentication schemes are case-insensitive while credentials are not."""

    application = create_app(
        RuntimeSettings(api_token="s3cret-token"),
        runtime_readiness_probe=lambda: True,
    )

    response = TestClient(application).post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": "bEaReR s3cret-token"},
    )

    assert response.status_code == 200
    assert parser_spy["count"] == 1


def test_required_mode_accepts_exact_header_byte_boundary(
    parser_spy: dict[str, int],
) -> None:
    """A valid complete credential exactly at the resource budget remains usable."""

    token = "a" * (MAX_BEARER_HEADER_BYTES - len(_BEARER_PREFIX))
    authorization = f"{_BEARER_PREFIX}{token}"
    assert len(authorization.encode("utf-8")) == MAX_BEARER_HEADER_BYTES
    application = create_app(
        RuntimeSettings(api_token=token),
        runtime_readiness_probe=lambda: True,
    )

    response = TestClient(application).post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": authorization},
    )

    assert response.status_code == 200
    assert parser_spy["count"] == 1


def test_runtime_settings_wrap_unencodable_secret_as_configuration_error() -> None:
    """Malformed Unicode in secret transport must fail with the public config type."""

    with pytest.raises(RuntimeConfigurationError, match="UTF-8"):
        RuntimeSettings(api_token="\ud800")


def test_ready_converts_probe_exception_to_fixed_unavailable_response() -> None:
    """Unexpected runtime-probe failures must fail closed without leaking details."""

    def failing_probe() -> bool:
        raise OSError("private executable path or operating-system detail")

    application = create_app(
        RuntimeSettings(api_token="s3cret-token"),
        runtime_readiness_probe=failing_probe,
    )

    response = TestClient(application, raise_server_exceptions=False).get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}
    assert "private" not in response.text.lower()
    assert "operating-system" not in response.text.lower()


def test_required_mode_compares_fixed_width_fingerprints_for_wrong_credentials(
    parser_spy: dict[str, int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wrong credential lengths must not change the secret-comparison width."""

    original_compare_digest = hmac.compare_digest
    comparison_widths: list[tuple[int, int]] = []

    def compare_digest_spy(left: bytes, right: bytes) -> bool:
        comparison_widths.append((len(left), len(right)))
        return original_compare_digest(left, right)

    monkeypatch.setattr("newsdom_api.main.hmac.compare_digest", compare_digest_spy)
    application = create_app(
        RuntimeSettings(api_token="s3cret-token-1234"),
        runtime_readiness_probe=lambda: True,
    )

    for credential in ("too-short", "w3rong-token-1234"):
        response = TestClient(application).post(
            "/parse",
            files=_PDF_FILES,
            headers={"Authorization": f"Bearer {credential}"},
        )
        assert response.status_code == 401

    digest_width = hashlib.sha256().digest_size
    assert comparison_widths == [(digest_width, digest_width)] * 2
    assert parser_spy["count"] == 0

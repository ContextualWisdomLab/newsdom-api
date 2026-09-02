"""Regression coverage for fixed-size authentication token comparison."""

from __future__ import annotations

import hashlib
import hmac

from fastapi.testclient import TestClient

import newsdom_api.main as main_module
from newsdom_api.config import RuntimeSettings
from newsdom_api.main import create_app


def test_runtime_settings_precomputes_fixed_size_token_digest() -> None:
    """The configured secret is normalized once outside the request path."""

    settings = RuntimeSettings(api_token="configured-token")

    assert settings.api_token_digest == hashlib.sha256(b"configured-token").digest()
    assert len(settings.api_token_digest or b"") == hashlib.sha256().digest_size


def test_mismatched_token_uses_equal_length_digest_operands(monkeypatch) -> None:
    """Request comparison never invokes compare_digest with secret-dependent lengths."""

    original_compare_digest = hmac.compare_digest
    operands: list[tuple[bytes, bytes]] = []

    def record_compare_digest(left: bytes, right: bytes) -> bool:
        operands.append((left, right))
        return original_compare_digest(left, right)

    monkeypatch.setattr(main_module.hmac, "compare_digest", record_compare_digest)
    client = TestClient(create_app(RuntimeSettings(api_token="configured-token")))

    response = client.post(
        "/parse",
        headers={"Authorization": "Bearer x"},
        files={"file": ("test.pdf", b"%PDF-1.4\n", "application/pdf")},
    )

    assert response.status_code == 401
    assert len(operands) == 1
    left, right = operands[0]
    assert len(left) == len(right) == hashlib.sha256().digest_size


def test_valid_token_still_authenticates_after_digest_normalization(monkeypatch) -> None:
    """Fixed-size comparison preserves exact configured-token acceptance."""

    monkeypatch.setattr(main_module, "parse_pdf", lambda *args, **kwargs: {"nodes": []})
    settings = RuntimeSettings(api_token="configured-token")
    client = TestClient(create_app(settings, runtime_readiness_probe=lambda: True))

    response = client.post(
        "/parse",
        headers={"Authorization": "Bearer configured-token"},
        files={"file": ("test.pdf", b"not-used", "application/pdf")},
    )

    # Authentication must not reject the exact token. The intentionally invalid
    # PDF may fail later at the media boundary, which is sufficient for this test.
    assert response.status_code != 401

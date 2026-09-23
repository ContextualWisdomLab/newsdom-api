"""Contract tests for bearer-token comparison behavior."""

from __future__ import annotations

import hmac

import pytest
from fastapi.testclient import TestClient

from newsdom_api.config import RuntimeSettings
from newsdom_api.main import create_app

_PDF_FILES = {
    "file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")
}


def test_mismatched_token_length_uses_equal_length_digest_operands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Length mismatch must fail closed without a differently sized digest compare."""

    expected = b"expected-token"
    observed: list[tuple[bytes, bytes]] = []
    original_compare_digest = hmac.compare_digest

    def recording_compare_digest(left: bytes, right: bytes) -> bool:
        observed.append((bytes(left), bytes(right)))
        return original_compare_digest(left, right)

    monkeypatch.setattr("newsdom_api.main.hmac.compare_digest", recording_compare_digest)
    application = create_app(
        RuntimeSettings(api_token=expected.decode("ascii")),
        runtime_readiness_probe=lambda: True,
    )

    response = TestClient(application).post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": "Bearer x"},
    )

    assert response.status_code == 401
    assert observed == [(expected, expected)]


def test_equal_length_wrong_token_compares_candidate_with_expected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Equal-length mismatches must retain the real constant-time comparison path."""

    expected = b"expected-token"
    candidate = b"x" * len(expected)
    observed: list[tuple[bytes, bytes]] = []
    original_compare_digest = hmac.compare_digest

    def recording_compare_digest(left: bytes, right: bytes) -> bool:
        observed.append((bytes(left), bytes(right)))
        return original_compare_digest(left, right)

    monkeypatch.setattr("newsdom_api.main.hmac.compare_digest", recording_compare_digest)
    application = create_app(
        RuntimeSettings(api_token=expected.decode("ascii")),
        runtime_readiness_probe=lambda: True,
    )

    response = TestClient(application).post(
        "/parse",
        files=_PDF_FILES,
        headers={"Authorization": f"Bearer {candidate.decode('ascii')}"},
    )

    assert response.status_code == 401
    assert observed == [(candidate, expected)]

"""Structural tests for bearer-token comparison operands."""

from __future__ import annotations

from fastapi.testclient import TestClient

from newsdom_api.config import RuntimeSettings
from newsdom_api.main import create_app


def _client() -> TestClient:
    """Build a required-mode application with one fixed bearer token."""

    return TestClient(
        create_app(
            RuntimeSettings(api_token="expected-token"),
            runtime_readiness_probe=lambda: True,
        )
    )


def test_wrong_length_token_still_invokes_equal_length_compare(monkeypatch) -> None:
    """Length-mismatch rejection must not call compare_digest with unequal operands."""

    calls: list[tuple[bytes, bytes]] = []

    def compare_probe(left: bytes, right: bytes) -> bool:
        calls.append((left, right))
        return left == right

    monkeypatch.setattr("newsdom_api.main.hmac.compare_digest", compare_probe)

    response = _client().post(
        "/parse",
        headers={"Authorization": "Bearer short"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    assert calls == [(b"short", b"short")]


def test_same_length_wrong_token_compares_against_expected_token(monkeypatch) -> None:
    """Equal-length hostile credentials must still be compared with the configured token."""

    calls: list[tuple[bytes, bytes]] = []

    def compare_probe(left: bytes, right: bytes) -> bool:
        calls.append((left, right))
        return left == right

    monkeypatch.setattr("newsdom_api.main.hmac.compare_digest", compare_probe)

    response = _client().post(
        "/parse",
        headers={"Authorization": "Bearer wrong-token---"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    assert calls == [(b"wrong-token---", b"expected-token")]

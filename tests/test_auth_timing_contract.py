"""Regression tests for bearer-token comparison timing structure."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from newsdom_api.config import (
    AuthenticationMode,
    RuntimeProfile,
    RuntimeSettings,
)
from newsdom_api.main import create_app


@pytest.mark.parametrize("credential", ["x", "x" * 64])
def test_wrong_length_bearer_uses_equal_length_compare_operands(
    monkeypatch: pytest.MonkeyPatch,
    credential: str,
) -> None:
    """Wrong-length credentials must not reach ``compare_digest`` with unequal sizes."""

    token = "s3cret-token"
    comparisons: list[tuple[bytes, bytes]] = []

    def recording_compare_digest(left: bytes, right: bytes) -> bool:
        comparisons.append((bytes(left), bytes(right)))
        return left == right

    monkeypatch.setattr(
        "newsdom_api.main.hmac.compare_digest",
        recording_compare_digest,
    )
    application = create_app(
        RuntimeSettings(
            authentication_mode=AuthenticationMode.REQUIRED,
            runtime_profile=RuntimeProfile.PRODUCTION,
            api_token=token,
        ),
        runtime_readiness_probe=lambda: True,
    )

    response = TestClient(application).post(
        "/parse",
        headers={"Authorization": f"Bearer {credential}"},
    )

    expected = token.encode("utf-8")
    assert response.status_code == 401
    assert comparisons == [(expected, expected)]

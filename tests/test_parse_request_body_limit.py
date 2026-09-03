"""Regression tests for the raw `/parse` request-body admission budget."""

from fastapi.testclient import TestClient

from newsdom_api.config import AuthenticationMode, RuntimeSettings
from newsdom_api.main import PAYLOAD_TOO_LARGE_DETAIL, create_app

_TEST_BODY_LIMIT = 1024


def _development_client() -> TestClient:
    """Create a parser client with a small injected body budget for fast tests."""
    application = create_app(
        RuntimeSettings(authentication_mode=AuthenticationMode.DISABLED),
        runtime_readiness_probe=lambda: True,
        max_request_body_bytes=_TEST_BODY_LIMIT,
    )
    return TestClient(application)


def test_parse_rejects_oversized_multipart_before_route_validation() -> None:
    """Reject multipart overhead and extra fields under one raw-body budget."""
    client = _development_client()
    response = client.post(
        "/parse",
        files={"file": ("tiny.pdf", b"%PDF-tiny", "application/pdf")},
        data={"language": "ch", "mode": "auto", "noise": "x" * 2048},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": PAYLOAD_TOO_LARGE_DETAIL}
    assert response.headers["x-content-type-options"] == "nosniff"


def test_parse_counts_received_bytes_when_content_length_is_understated() -> None:
    """Do not trust a smaller Content-Length than the bytes actually received."""
    client = _development_client()
    body = b"x" * (_TEST_BODY_LIMIT + 1)
    response = client.post(
        "/parse",
        content=body,
        headers={
            "content-type": "application/octet-stream",
            "content-length": "1",
        },
    )

    assert response.status_code == 413
    assert response.json() == {"detail": PAYLOAD_TOO_LARGE_DETAIL}
    assert response.headers["content-security-policy"] == (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )

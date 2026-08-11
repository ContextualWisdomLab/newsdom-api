"""Regression contracts for HTTP exception security handling."""

from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from newsdom_api.config import RuntimeSettings
from newsdom_api.main import custom_http_exception_handler, create_app


def test_starlette_http_errors_share_the_security_handler() -> None:
    """Framework-generated 404 and 405 responses use the secured handler."""

    application = create_app(
        RuntimeSettings(api_token="test-token"),
        runtime_readiness_probe=lambda: True,
    )

    assert (
        application.exception_handlers[StarletteHTTPException]
        is custom_http_exception_handler
    )

    with TestClient(application) as client:
        missing = client.get("/missing")
        method_not_allowed = client.post("/health")

    for response, expected_status in ((missing, 404), (method_not_allowed, 405)):
        assert response.status_code == expected_status
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Content-Security-Policy"] == (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        assert response.headers["Referrer-Policy"] == "no-referrer"
        assert response.headers["Cache-Control"] == "no-store, no-cache, max-age=0"

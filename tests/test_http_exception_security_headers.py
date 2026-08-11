"""Regression contracts for HTTP exception security handling."""

from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from newsdom_api.config import RuntimeSettings
from newsdom_api.main import custom_http_exception_handler, create_app

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store, no-cache, max-age=0",
}


def test_starlette_and_application_http_errors_share_the_security_handler() -> None:
    """Routing and application errors preserve details, headers, and security."""

    application = create_app(
        RuntimeSettings(api_token="test-token"),
        runtime_readiness_probe=lambda: True,
    )

    def application_error() -> None:
        raise HTTPException(
            status_code=418,
            detail="application error",
            headers={"X-Error-Context": "preserved"},
        )

    application.add_api_route("/application-error", application_error, methods=["GET"])

    assert (
        application.exception_handlers[StarletteHTTPException]
        is custom_http_exception_handler
    )

    with TestClient(application, base_url="https://testserver") as client:
        responses = (
            (client.get("/missing"), 404, "Not Found"),
            (client.post("/health"), 405, "Method Not Allowed"),
            (client.get("/application-error"), 418, "application error"),
        )

    for response, expected_status, expected_detail in responses:
        assert response.status_code == expected_status
        assert response.json() == {"detail": expected_detail}
        for header, expected_value in _SECURITY_HEADERS.items():
            assert response.headers[header] == expected_value
        assert response.headers["Strict-Transport-Security"] == (
            "max-age=31536000; includeSubDomains"
        )

    assert responses[-1][0].headers["X-Error-Context"] == "preserved"


def test_http_exception_handler_omits_hsts_for_plain_http() -> None:
    """HTTP error responses do not claim transport security without HTTPS."""

    application = create_app(
        RuntimeSettings(api_token="test-token"),
        runtime_readiness_probe=lambda: True,
    )

    with TestClient(application, base_url="http://testserver") as client:
        response = client.get("/missing")

    assert response.status_code == 404
    assert "Strict-Transport-Security" not in response.headers

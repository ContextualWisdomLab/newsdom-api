from fastapi.testclient import TestClient

from newsdom_api.main import app


def test_http_exception_handler_applies_security_headers() -> None:
    """Verify that Starlette HTTPExceptions receive security headers."""
    client = TestClient(app, raise_server_exceptions=False)

    # 404 Not Found (Native Starlette HTTPException)
    response = client.get("/non_existent_route")
    assert response.status_code == 404
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"

    # 401 Unauthorized (Triggered by missing token but with disabled auth we get 503 if we don't mock it, wait, we can just trigger 422)
    # 422 Unprocessable Entity (FastAPI validation error, but uses RequestValidationError, which bubbles up differently, wait. Let's just test 405 Method Not Allowed)
    response_405 = client.post("/health")
    assert response_405.status_code == 405
    assert response_405.headers.get("x-content-type-options") == "nosniff"
    assert response_405.headers.get("x-frame-options") == "DENY"

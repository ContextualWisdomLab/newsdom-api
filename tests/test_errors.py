from fastapi.testclient import TestClient

from newsdom_api.errors import (
    MineruIncompleteOutputError,
    MineruRuntimeUnavailableError,
)
from newsdom_api.main import app


def test_http_exception_handler_headers():
    """Ensure HTTPExceptions receive standard security headers."""
    client = TestClient(app, raise_server_exceptions=False)
    # 404 is a standard StarletteHTTPException
    response = client.get("/nonexistent_endpoint")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_validation_exception_handler_headers():
    """Ensure RequestValidationErrors receive standard security headers."""
    client = TestClient(app, raise_server_exceptions=False)
    # Send empty payload to trigger a validation error
    response = client.post("/parse")
    assert response.status_code == 422
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_http_exception_handler_no_body_headers():
    """Ensure HTTPExceptions with no-body status codes receive headers."""
    from fastapi import FastAPI
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from newsdom_api.main import http_exception_handler

    test_app = FastAPI()
    test_app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    @test_app.get("/raise_204")
    def raise_204():
        raise StarletteHTTPException(status_code=204)

    client = TestClient(test_app, raise_server_exceptions=False)
    response = client.get("/raise_204")
    assert response.status_code == 204
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    # Ensure there is no response body
    assert not response.content


def test_mineru_runtime_unavailable_error_initialization():
    """Ensure MineruRuntimeUnavailableError initializes correctly."""
    error = MineruRuntimeUnavailableError(
        returncode=1,
        stdout="stdout text",
        stderr="stderr text",
    )
    assert error.returncode == 1
    assert error.stdout == "stdout text"
    assert error.stderr == "stderr text"
    assert str(error) == "MinerU runtime unavailable"


def test_mineru_incomplete_output_error_initialization():
    """Ensure MineruIncompleteOutputError initializes correctly."""
    error = MineruIncompleteOutputError()
    assert str(error) == "MinerU output was incomplete"

from newsdom_api.errors import (
    MineruIncompleteOutputError,
    MineruRuntimeUnavailableError,
)
from fastapi.testclient import TestClient
from fastapi import Request
from newsdom_api.main import create_app, global_exception_handler
import pytest


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(), raise_server_exceptions=False)


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


def test_http_exception_handler_headers(client: TestClient) -> None:
    """Ensure StarletteHTTPException includes security headers."""

    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert (
        response.headers["Content-Security-Policy"]
        == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )


def test_validation_exception_handler_headers(client: TestClient) -> None:
    """Ensure RequestValidationError includes security headers."""

    # Send a POST with an invalid language to trigger validation error
    response = client.post("/parse", data={"language": 123, "mode": "invalid"})
    assert response.status_code == 422
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert (
        response.headers["Content-Security-Policy"]
        == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )


@pytest.mark.asyncio
async def test_global_exception_handler_headers_direct():
    """Test the global exception handler directly."""
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"host", b"testserver")],
            "scheme": "http",
        }
    )
    exc = RuntimeError("Test Error")

    response = await global_exception_handler(request, exc)
    assert response.status_code == 500
    assert response.headers["X-Content-Type-Options"] == "nosniff"

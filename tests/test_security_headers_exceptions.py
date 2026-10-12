import pytest
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.newsdom_api.config import RuntimeSettings, AuthenticationMode, RuntimeProfile
from src.newsdom_api.main import create_app


@pytest.fixture
def test_client():
    settings = RuntimeSettings(
        api_token=None,
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
    )
    # Using real app router but we override readiness for testing
    app = create_app(settings, runtime_readiness_probe=lambda: True)

    # Add a dummy route that raises an exception with a status code that does not allow a body
    @app.get("/no-content-exception")
    def no_content_exception():
        raise StarletteHTTPException(status_code=204)

    return TestClient(app, raise_server_exceptions=False)


def test_http_exception_no_body(test_client):
    response = test_client.get("/no-content-exception")
    assert response.status_code == 204
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.content == b""

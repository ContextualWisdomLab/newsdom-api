import pytest
from fastapi.testclient import TestClient
from src.newsdom_api.main import create_app


@pytest.fixture(scope="module")
def unauth_client():
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def test_http_exception_headers(unauth_client: TestClient):
    response = unauth_client.get("/nonexistent")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"


def test_validation_error_headers(unauth_client: TestClient):
    response = unauth_client.post("/parse", data={})
    assert response.status_code == 422
    assert response.headers.get("X-Content-Type-Options") == "nosniff"

from fastapi.testclient import TestClient
from newsdom_api.main import app, create_app
from newsdom_api.config import RuntimeSettings, AuthenticationMode, RuntimeProfile

def test_docs_csp_loosened():
    client = TestClient(app)
    response = client.get("/docs")
    assert " cdn.jsdelivr.net; " in response.headers["Content-Security-Policy"]

def test_persist_auth_dev_only():
    dev_settings = RuntimeSettings(runtime_profile=RuntimeProfile.DEVELOPMENT)
    dev_app = create_app(dev_settings)
    assert dev_app.swagger_ui_parameters.get("persistAuthorization") is True

    prod_settings = RuntimeSettings(runtime_profile=RuntimeProfile.PRODUCTION)
    prod_app = create_app(prod_settings)
    assert prod_app.swagger_ui_parameters.get("persistAuthorization") is not True

def test_docs_logout_path_exists():
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200

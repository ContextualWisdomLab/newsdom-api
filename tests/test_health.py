from fastapi.testclient import TestClient

from newsdom_api.main import app


def test_healthcheck():
    client = TestClient(app, base_url="https://testserver")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Verify security headers are injected by middleware
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert (
        response.headers.get("Content-Security-Policy")
        == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )
    assert response.headers.get("Referrer-Policy") == "no-referrer"
    assert response.headers.get("Cache-Control") == "no-store, no-cache, max-age=0"
    assert (
        response.headers.get("Strict-Transport-Security")
        == "max-age=31536000; includeSubDomains"
    )


def test_healthcheck_omits_hsts_for_plain_http():
    client = TestClient(app, base_url="http://testserver")
    response = client.get("/health")

    assert response.status_code == 200
    assert "Strict-Transport-Security" not in response.headers


def test_healthcheck_emits_hsts_for_forwarded_https():
    client = TestClient(app, base_url="http://testserver")
    response = client.get("/health", headers={"X-Forwarded-Proto": "https"})

    assert response.status_code == 200
    assert (
        response.headers.get("Strict-Transport-Security")
        == "max-age=31536000; includeSubDomains"
    )


def test_openapi_metadata_includes_contact_and_license():
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    info = response.json()["info"]
    assert info["contact"] == {
        "name": "Seongho Bae",
        "url": "https://github.com/ContextualWisdomLab/newsdom-api",
    }
    assert info["license"] == {
        "name": "MIT License",
        "identifier": "MIT",
    }

def test_swagger_ui_parameters_persist_authorization_in_development():
    from newsdom_api.main import create_app
    from newsdom_api.config import RuntimeSettings, RuntimeProfile, AuthenticationMode

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT
    )
    dev_app = create_app(settings)
    assert dev_app.swagger_ui_parameters is not None
    assert dev_app.swagger_ui_parameters.get("persistAuthorization") is True

def test_swagger_ui_parameters_no_persist_authorization_in_production():
    from newsdom_api.main import create_app
    from newsdom_api.config import RuntimeSettings, RuntimeProfile, AuthenticationMode

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token="test_token"
    )
    prod_app = create_app(settings)
    assert prod_app.swagger_ui_parameters is not None
    assert "persistAuthorization" not in prod_app.swagger_ui_parameters

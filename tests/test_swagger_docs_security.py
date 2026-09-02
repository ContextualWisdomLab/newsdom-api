"""Regression tests for the Swagger UI authentication and CSP boundary."""

from fastapi.testclient import TestClient

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app

LOCKED_DOWN_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


def _settings(profile: RuntimeProfile) -> RuntimeSettings:
    """Build an authenticated runtime configuration for one profile."""

    return RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=profile,
        api_token="swagger-test-token",
    )


def test_swagger_authorization_persistence_is_development_only() -> None:
    """Persist bearer authorization only in the explicit development profile."""

    production = TestClient(create_app(_settings(RuntimeProfile.PRODUCTION)))
    development = TestClient(create_app(_settings(RuntimeProfile.DEVELOPMENT)))

    production_docs = production.get("/docs")
    development_docs = development.get("/docs")

    assert production_docs.status_code == 200
    assert development_docs.status_code == 200
    assert '"persistAuthorization": false' in production_docs.text
    assert '"persistAuthorization": true' in development_docs.text


def test_development_docs_csp_allows_only_required_swagger_origins() -> None:
    """Development Swagger UI can execute while retaining a narrow CSP."""

    client = TestClient(create_app(_settings(RuntimeProfile.DEVELOPMENT)))
    response = client.get("/docs")

    assert response.status_code == 200
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    assert "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net" in csp
    assert "style-src 'self' https://cdn.jsdelivr.net" in csp
    assert "img-src 'self' data: https://fastapi.tiangolo.com" in csp
    assert "connect-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'none'" in csp
    assert "form-action 'self'" in csp


def test_non_docs_responses_keep_the_locked_down_csp() -> None:
    """The docs exception must not weaken the API response security boundary."""

    client = TestClient(
        create_app(_settings(RuntimeProfile.DEVELOPMENT)),
        base_url="https://testserver",
    )
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["Content-Security-Policy"] == LOCKED_DOWN_CSP

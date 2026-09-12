"""Security-boundary regressions for the development-only Swagger UI surface."""

from fastapi.testclient import TestClient

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app


_STRICT_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


def _settings(profile: RuntimeProfile) -> RuntimeSettings:
    """Build the minimum valid runtime settings for one profile."""

    if profile is RuntimeProfile.DEVELOPMENT:
        return RuntimeSettings(
            authentication_mode=AuthenticationMode.DISABLED,
            runtime_profile=profile,
        )
    return RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=profile,
        api_token="test-token",
    )


def test_production_docs_do_not_relax_the_content_security_policy() -> None:
    """Production documentation must not inherit the development CDN/inline policy."""

    response = TestClient(create_app(_settings(RuntimeProfile.PRODUCTION))).get("/docs")

    assert response.status_code == 200
    assert response.headers["Content-Security-Policy"] == _STRICT_CSP


def test_development_docs_keep_frame_and_base_uri_denial_when_relaxed() -> None:
    """Development Swagger resources may relax CSP without dropping invariant guards."""

    response = TestClient(create_app(_settings(RuntimeProfile.DEVELOPMENT))).get("/docs")
    policy = response.headers["Content-Security-Policy"]

    assert response.status_code == 200
    assert "cdn.jsdelivr.net" in policy
    assert "frame-ancestors 'none'" in policy
    assert "base-uri 'none'" in policy

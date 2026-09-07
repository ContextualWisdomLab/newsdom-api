"""Tests for Developer Experience enhancements in the OpenAPI documentation endpoints."""

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app

def test_swagger_persist_authorization_enabled_in_development() -> None:
    """Ensure Developer Experience features are enabled strictly in development."""
    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
        api_token="dummy",
    )
    application = create_app(settings)
    assert application.swagger_ui_parameters is not None
    assert application.swagger_ui_parameters.get("persistAuthorization") is True

def test_swagger_persist_authorization_disabled_in_production() -> None:
    """Ensure production environments do not leak persistent credentials across sessions."""
    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token="dummy",
    )
    application = create_app(settings)
    if application.swagger_ui_parameters is not None:
        assert "persistAuthorization" not in application.swagger_ui_parameters

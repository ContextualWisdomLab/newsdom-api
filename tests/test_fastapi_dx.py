from fastapi.testclient import TestClient
from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app

def test_development_profile_persists_authorization():
    """Verify persistAuthorization is enabled in development profile."""
    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
    )
    app = create_app(settings)
    assert app.swagger_ui_parameters.get("persistAuthorization") is True

def test_production_profile_does_not_persist_authorization():
    """Verify persistAuthorization is not enabled in production profile."""
    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token="test_token"
    )
    app = create_app(settings)
    assert app.swagger_ui_parameters.get("persistAuthorization") is None

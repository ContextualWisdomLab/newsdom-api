from fastapi.testclient import TestClient
from newsdom_api.main import app
from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app

import pytest
from newsdom_api.config import RuntimeConfigurationError

def test_development_profile_persists_authorization_default_off():
    """Verify persistAuthorization is off by default even in development profile."""
    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
    )
    app = create_app(settings)
    assert app.swagger_ui_parameters.get("persistAuthorization") is None

def test_development_profile_persists_authorization_opt_in():
    """Verify persistAuthorization is enabled in development profile when explicitly requested."""
    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
        persist_authorization=True,
    )
    app = create_app(settings)
    assert app.swagger_ui_parameters.get("persistAuthorization") is True

def test_production_profile_does_not_persist_authorization():
    """Verify persistAuthorization is off by default in production profile."""
    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token="test_token"
    )
    app = create_app(settings)
    assert app.swagger_ui_parameters.get("persistAuthorization") is None

def test_production_profile_rejects_persist_authorization():
    """Verify persistAuthorization explicitly requested in production fails closed."""
    with pytest.raises(RuntimeConfigurationError, match="development runtime profile"):
        RuntimeSettings(
            authentication_mode=AuthenticationMode.REQUIRED,
            runtime_profile=RuntimeProfile.PRODUCTION,
            api_token="test_token",
            persist_authorization=True,
        )

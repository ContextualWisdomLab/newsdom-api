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

from newsdom_api.config import load_runtime_settings

def test_load_settings_parses_persist_authorization_env_var():
    """Verify persist_authorization is loaded from NEWSDOM_SWAGGER_PERSIST_AUTHORIZATION."""
    env = {
        "NEWSDOM_AUTH_MODE": "disabled",
        "NEWSDOM_RUNTIME_PROFILE": "development",
        "NEWSDOM_SWAGGER_PERSIST_AUTHORIZATION": "true"
    }
    settings = load_runtime_settings(env)
    assert settings.persist_authorization is True

def test_production_profile_auth_readiness_is_unchanged():
    """Verify unchanged production auth readiness."""
    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token="test_token"
    )
    assert settings.authentication_ready is True

    settings_missing_token = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
    )
    assert settings_missing_token.authentication_ready is False

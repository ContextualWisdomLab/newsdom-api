"""Swagger UI credential-persistence boundary regressions."""

import pytest

from newsdom_api.config import (
    AuthenticationMode,
    RuntimeConfigurationError,
    RuntimeProfile,
    RuntimeSettings,
    load_runtime_settings,
)
from newsdom_api.main import create_app


def test_development_profile_defaults_to_no_authorization_persistence() -> None:
    """A development profile alone must not authorize browser credential storage."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
    )

    app = create_app(settings)

    assert app.swagger_ui_parameters.get("persistAuthorization") is not True


def test_development_profile_requires_explicit_persistence_opt_in() -> None:
    """An explicit development-only setting may enable Swagger credential persistence."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
        api_token="test_token",
        swagger_persist_authorization=True,
    )

    app = create_app(settings)

    assert app.swagger_ui_parameters.get("persistAuthorization") is True


def test_production_profile_rejects_persistence_opt_in() -> None:
    """Production must fail closed when browser credential persistence is requested."""

    with pytest.raises(RuntimeConfigurationError):
        RuntimeSettings(
            authentication_mode=AuthenticationMode.REQUIRED,
            runtime_profile=RuntimeProfile.PRODUCTION,
            api_token="test_token",
            swagger_persist_authorization=True,
        )


def test_environment_persistence_opt_in_is_explicit_and_development_only() -> None:
    """The operator-facing environment boundary must expose the opt-in explicitly."""

    settings = load_runtime_settings(
        {
            "NEWSDOM_AUTH_MODE": "required",
            "NEWSDOM_RUNTIME_PROFILE": "development",
            "NEWSDOM_API_TOKEN": "test_token",
            "NEWSDOM_SWAGGER_PERSIST_AUTHORIZATION": "true",
        }
    )

    assert settings.swagger_persist_authorization is True

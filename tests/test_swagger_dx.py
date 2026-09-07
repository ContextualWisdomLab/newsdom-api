"""Tests for Developer Experience enhancements in the OpenAPI documentation endpoints."""

import pytest

from newsdom_api.config import (
    API_TOKEN_ENV_VAR,
    RUNTIME_PROFILE_ENV_VAR,
    SWAGGER_PERSIST_AUTHORIZATION_ENV_VAR,
    AuthenticationMode,
    RuntimeConfigurationError,
    RuntimeProfile,
    RuntimeSettings,
    load_runtime_settings,
)
from newsdom_api.main import create_app


def test_swagger_persist_authorization_disabled_by_default_in_development() -> None:
    """Development must not persist entered bearer credentials without explicit opt-in."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
        api_token="dummy",
    )
    application = create_app(settings)

    assert application.swagger_ui_parameters is not None
    assert application.swagger_ui_parameters.get("persistAuthorization") is None


def test_swagger_persist_authorization_requires_explicit_development_opt_in() -> None:
    """An explicit development-only opt-in may retain Swagger authorization state."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
        api_token="dummy",
        swagger_persist_authorization=True,
    )
    application = create_app(settings)

    assert application.swagger_ui_parameters is not None
    assert application.swagger_ui_parameters.get("persistAuthorization") is True


def test_swagger_persist_authorization_env_opt_in_is_operational() -> None:
    """The documented runtime flag should reach the immutable application settings."""

    settings = load_runtime_settings(
        {
            API_TOKEN_ENV_VAR: "dummy",
            RUNTIME_PROFILE_ENV_VAR: "development",
            SWAGGER_PERSIST_AUTHORIZATION_ENV_VAR: "true",
        }
    )
    application = create_app(settings)

    assert settings.swagger_persist_authorization is True
    assert application.swagger_ui_parameters is not None
    assert application.swagger_ui_parameters.get("persistAuthorization") is True


def test_swagger_persist_authorization_rejected_in_production() -> None:
    """Production must reject persistent browser authorization even when requested."""

    with pytest.raises(RuntimeConfigurationError, match="development"):
        RuntimeSettings(
            authentication_mode=AuthenticationMode.REQUIRED,
            runtime_profile=RuntimeProfile.PRODUCTION,
            api_token="dummy",
            swagger_persist_authorization=True,
        )


def test_swagger_persist_authorization_rejects_ambiguous_boolean() -> None:
    """Unknown boolean spellings must not silently enable credential persistence."""

    with pytest.raises(
        RuntimeConfigurationError, match=SWAGGER_PERSIST_AUTHORIZATION_ENV_VAR
    ):
        load_runtime_settings(
            {
                API_TOKEN_ENV_VAR: "dummy",
                RUNTIME_PROFILE_ENV_VAR: "development",
                SWAGGER_PERSIST_AUTHORIZATION_ENV_VAR: "yes",
            }
        )

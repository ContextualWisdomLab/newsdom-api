"""Tests for Swagger/OpenAPI developer-experience runtime controls."""

import pytest

from newsdom_api.config import (
    PERSIST_AUTHORIZATION_ENV_VAR,
    AuthenticationMode,
    RuntimeConfigurationError,
    RuntimeProfile,
    RuntimeSettings,
    load_runtime_settings,
)
from newsdom_api.main import create_app


def test_development_profile_persists_authorization_default_off() -> None:
    """Development must not persist authorization without explicit operator opt-in."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
    )

    application = create_app(settings)

    assert "persistAuthorization" not in application.swagger_ui_parameters


def test_development_profile_persists_authorization_opt_in() -> None:
    """Development may persist authorization when the operator explicitly opts in."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
        persist_authorization=True,
    )

    application = create_app(settings)

    assert application.swagger_ui_parameters["persistAuthorization"] is True


def test_production_profile_does_not_persist_authorization() -> None:
    """Production must omit the browser credential-persistence option by default."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token="test_token",  # noqa: S106 - intentional non-secret test credential
    )

    application = create_app(settings)

    assert "persistAuthorization" not in application.swagger_ui_parameters


def test_production_profile_rejects_persist_authorization() -> None:
    """Production must fail closed when authorization persistence is requested."""

    with pytest.raises(RuntimeConfigurationError, match="development runtime profile"):
        RuntimeSettings(
            authentication_mode=AuthenticationMode.REQUIRED,
            runtime_profile=RuntimeProfile.PRODUCTION,
            api_token="test_token",  # noqa: S106 - intentional non-secret test credential
            persist_authorization=True,
        )


def test_load_settings_parses_persist_authorization_env_var() -> None:
    """The documented environment opt-in must reach immutable runtime settings."""

    settings = load_runtime_settings(
        {
            "NEWSDOM_AUTH_MODE": "disabled",
            "NEWSDOM_RUNTIME_PROFILE": "development",
            PERSIST_AUTHORIZATION_ENV_VAR: "true",
        }
    )

    assert settings.persist_authorization is True


def test_production_environment_rejects_persist_authorization() -> None:
    """The environment loader must enforce the same production fail-closed boundary."""

    with pytest.raises(RuntimeConfigurationError, match="development runtime profile"):
        load_runtime_settings(
            {
                "NEWSDOM_RUNTIME_PROFILE": "production",
                PERSIST_AUTHORIZATION_ENV_VAR: "true",
            }
        )


def test_production_profile_auth_readiness_is_unchanged() -> None:
    """The Swagger option must not alter the parser-authentication readiness contract."""

    configured = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token="test_token",  # noqa: S106 - intentional non-secret test credential
    )
    missing_token = RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
    )

    assert configured.authentication_ready is True
    assert missing_token.authentication_ready is False

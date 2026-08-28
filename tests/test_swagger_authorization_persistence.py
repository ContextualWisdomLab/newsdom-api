"""Tests for the Swagger UI authorization-lifetime boundary."""

from __future__ import annotations

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app


def _settings(*, profile: RuntimeProfile) -> RuntimeSettings:
    """Build authenticated settings for one explicit runtime profile."""

    return RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=profile,
        api_token="docs-test-token",
    )


def test_production_docs_do_not_persist_authorization_across_refreshes() -> None:
    """Protected profiles must keep Swagger authorization persistence disabled."""

    application = create_app(
        _settings(profile=RuntimeProfile.PRODUCTION),
        runtime_readiness_probe=lambda: True,
    )

    assert application.swagger_ui_parameters["persistAuthorization"] is False
    assert (
        "Re-enter your Bearer token after refreshing this page."
        in application.description
    )


def test_development_docs_may_persist_authorization_across_refreshes() -> None:
    """Only the explicit development profile may retain Swagger authorization."""

    application = create_app(
        _settings(profile=RuntimeProfile.DEVELOPMENT),
        runtime_readiness_probe=lambda: True,
    )

    assert application.swagger_ui_parameters["persistAuthorization"] is True
    assert "explicit development profile" in application.description

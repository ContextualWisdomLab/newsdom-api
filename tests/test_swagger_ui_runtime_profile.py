"""Swagger UI settings that must remain bounded to the development profile."""

from newsdom_api.config import RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app


def test_persist_authorization_is_enabled_only_for_development() -> None:
    """Persist Swagger credentials only when the runtime profile is development."""

    development = create_app(
        RuntimeSettings(
            runtime_profile=RuntimeProfile.DEVELOPMENT,
            api_token="development-token",
        ),
        runtime_readiness_probe=lambda: True,
    )
    production = create_app(
        RuntimeSettings(
            runtime_profile=RuntimeProfile.PRODUCTION,
            api_token="production-token",
        ),
        runtime_readiness_probe=lambda: True,
    )

    assert development.swagger_ui_parameters["persistAuthorization"] is True
    assert "persistAuthorization" not in production.swagger_ui_parameters

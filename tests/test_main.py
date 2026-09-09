from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app


def test_swagger_ui_persists_authorization_only_in_development() -> None:
    development_app = create_app(
        RuntimeSettings(
            authentication_mode=AuthenticationMode.DISABLED,
            runtime_profile=RuntimeProfile.DEVELOPMENT,
        )
    )
    production_app = create_app(
        RuntimeSettings(
            authentication_mode=AuthenticationMode.REQUIRED,
            runtime_profile=RuntimeProfile.PRODUCTION,
            api_token="test-token",
        )
    )

    assert development_app.swagger_ui_parameters is not None
    assert development_app.swagger_ui_parameters.get("persistAuthorization") is True
    assert production_app.swagger_ui_parameters is not None
    assert production_app.swagger_ui_parameters.get("persistAuthorization") is None

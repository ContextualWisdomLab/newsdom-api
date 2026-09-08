import pytest
from fastapi.testclient import TestClient

from newsdom_api.config import RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app

def test_swagger_ui_persist_authorization_in_development():
    """Verify that Swagger UI persistAuthorization is True in the development profile."""
    # Arrange
    settings = RuntimeSettings(
        authentication_mode="disabled",
        runtime_profile=RuntimeProfile.DEVELOPMENT
    )

    # Act
    app = create_app(settings)

    # Assert
    assert app.swagger_ui_parameters is not None
    assert app.swagger_ui_parameters.get("persistAuthorization") is True

def test_swagger_ui_persist_authorization_not_in_production():
    """Verify that Swagger UI persistAuthorization is not set in the production profile."""
    # Arrange
    settings = RuntimeSettings(
        authentication_mode="required",
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token="test-token"
    )

    # Act
    app = create_app(settings)

    # Assert
    assert app.swagger_ui_parameters is not None
    assert app.swagger_ui_parameters.get("persistAuthorization") is None

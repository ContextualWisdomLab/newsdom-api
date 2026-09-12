"""Swagger UI security and developer-experience configuration tests."""

from __future__ import annotations

import pytest

from newsdom_api.config import RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app


@pytest.mark.parametrize(
    ("profile", "expected_persistence"),
    [
        (RuntimeProfile.PRODUCTION, False),
        (RuntimeProfile.DEVELOPMENT, True),
    ],
)
def test_authorization_persistence_is_development_only(
    profile: RuntimeProfile, expected_persistence: bool
) -> None:
    """Browser authorization state persists only in the explicit development profile."""

    application = create_app(
        RuntimeSettings(runtime_profile=profile, api_token="swagger-test-token"),
        runtime_readiness_probe=lambda: True,
    )

    assert application.swagger_ui_parameters["persistAuthorization"] is expected_persistence

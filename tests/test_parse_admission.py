"""Contracts for process-local parser admission control."""

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app


def _development_settings(*, capacity: int) -> RuntimeSettings:
    """Return explicit development settings for one admission-control test."""

    return RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
        max_concurrent_parses=capacity,
    )


def test_application_binds_configured_process_local_parse_capacity() -> None:
    """Each application should own the immutable parse capacity it was given."""

    application = create_app(
        _development_settings(capacity=3),
        runtime_readiness_probe=lambda: True,
    )

    assert application.state.parse_admission_limiter.capacity == 3

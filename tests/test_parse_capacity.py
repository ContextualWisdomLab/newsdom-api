"""Contracts for bounded parser admission control."""

from newsdom_api.config import RuntimeSettings


def test_runtime_settings_default_to_one_concurrent_parse() -> None:
    """A standalone process should admit one expensive parse by default."""

    settings = RuntimeSettings()

    assert settings.max_concurrent_parses == 1

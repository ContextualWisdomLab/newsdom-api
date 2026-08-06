"""Contracts for bounded parser admission control."""

from newsdom_api.config import RuntimeSettings, load_runtime_settings


def test_runtime_settings_default_to_one_concurrent_parse() -> None:
    """A standalone process should admit one expensive parse by default."""

    settings = RuntimeSettings()

    assert settings.max_concurrent_parses == 1


def test_runtime_settings_load_configured_parse_capacity() -> None:
    """Operators should be able to set a bounded per-process parse budget."""

    settings = load_runtime_settings({"NEWSDOM_MAX_CONCURRENT_PARSES": "8"})

    assert settings.max_concurrent_parses == 8

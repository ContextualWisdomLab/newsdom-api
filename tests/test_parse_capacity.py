"""Contracts for bounded parser admission control."""

import pytest

from newsdom_api.config import (
    RuntimeConfigurationError,
    RuntimeSettings,
    load_runtime_settings,
)


def test_runtime_settings_default_to_one_concurrent_parse() -> None:
    """A standalone process should admit one expensive parse by default."""

    settings = RuntimeSettings()

    assert settings.max_concurrent_parses == 1


def test_runtime_settings_load_configured_parse_capacity() -> None:
    """Operators should be able to set a bounded per-process parse budget."""

    settings = load_runtime_settings({"NEWSDOM_MAX_CONCURRENT_PARSES": "8"})

    assert settings.max_concurrent_parses == 8


@pytest.mark.parametrize("raw_value", ["", "0", "129", "not-an-integer"])
def test_runtime_settings_reject_invalid_environment_capacity(raw_value: str) -> None:
    """Environment input must be an integer in the supported process range."""

    with pytest.raises(RuntimeConfigurationError, match="NEWSDOM_MAX_CONCURRENT_PARSES"):
        load_runtime_settings({"NEWSDOM_MAX_CONCURRENT_PARSES": raw_value})


@pytest.mark.parametrize("capacity", [0, 129, True])
def test_runtime_settings_reject_invalid_direct_capacity(capacity: object) -> None:
    """Direct construction must preserve the same immutable capacity boundary."""

    with pytest.raises(RuntimeConfigurationError, match="NEWSDOM_MAX_CONCURRENT_PARSES"):
        RuntimeSettings(max_concurrent_parses=capacity)  # type: ignore[arg-type]

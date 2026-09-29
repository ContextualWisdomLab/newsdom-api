"""Immutable runtime configuration for the standalone NewsDOM sidecar."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

API_TOKEN_ENV_VAR = "NEWSDOM_API_TOKEN"
AUTH_MODE_ENV_VAR = "NEWSDOM_AUTH_MODE"
RUNTIME_PROFILE_ENV_VAR = "NEWSDOM_RUNTIME_PROFILE"
MAX_BEARER_HEADER_BYTES = 4096


class RuntimeConfigurationError(ValueError):
    """Raised when runtime settings violate a fail-closed service boundary."""


class AuthenticationMode(str, Enum):
    """Supported parser authentication modes."""

    REQUIRED = "required"
    DISABLED = "disabled"


class RuntimeProfile(str, Enum):
    """Runtime profiles that determine whether development bypasses are valid."""

    PRODUCTION = "production"
    DEVELOPMENT = "development"


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Validated settings frozen for the lifetime of one FastAPI application."""

    authentication_mode: AuthenticationMode = AuthenticationMode.REQUIRED
    runtime_profile: RuntimeProfile = RuntimeProfile.PRODUCTION
    api_token: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Normalize secrets once and reject unsafe direct construction."""

        if (
            self.authentication_mode is AuthenticationMode.DISABLED
            and self.runtime_profile is not RuntimeProfile.DEVELOPMENT
        ):
            raise RuntimeConfigurationError(
                "Authentication can be disabled only in the development runtime profile"
            )

        if self.api_token is None:
            return

        normalized_token = self.api_token.strip()
        if not normalized_token:
            raise RuntimeConfigurationError(
                "The configured parser authentication token must not be blank"
            )
        try:
            bearer_value = f"Bearer {normalized_token}".encode("utf-8")
        except UnicodeEncodeError as exc:
            raise RuntimeConfigurationError(
                "The configured parser authentication token must be valid UTF-8"
            ) from exc
        if len(bearer_value) > MAX_BEARER_HEADER_BYTES:
            raise RuntimeConfigurationError(
                "The configured parser authentication token is too long"
            )
        object.__setattr__(self, "api_token", normalized_token)

    @property
    def authentication_ready(self) -> bool:
        """Return whether the authentication configuration can serve traffic safely."""

        return (
            self.authentication_mode is AuthenticationMode.DISABLED
            or self.api_token is not None
        )


def _parse_enum_value(
    source: Mapping[str, str],
    variable: str,
    enum_type: type[Enum],
    default: str,
) -> str:
    """Parse one normalized enum setting or raise a non-sensitive error."""

    raw = source.get(variable, default).strip().lower()
    try:
        enum_type(raw)
    except ValueError as exc:
        raise RuntimeConfigurationError(
            f"Invalid value for {variable}; use one of the documented modes"
        ) from exc
    return raw


def get_api_token(source: Mapping[str, str] | None = None) -> str | None:
    """Return a normalized bootstrap token without logging or exposing it."""

    values = os.environ if source is None else source
    raw = values.get(API_TOKEN_ENV_VAR)
    if raw is None:
        return None
    token = raw.strip()
    return token or None


def load_runtime_settings(
    source: Mapping[str, str] | None = None,
) -> RuntimeSettings:
    """Load and validate a single immutable application configuration snapshot."""

    values = os.environ if source is None else source
    authentication_mode = AuthenticationMode(
        _parse_enum_value(
            values,
            AUTH_MODE_ENV_VAR,
            AuthenticationMode,
            AuthenticationMode.REQUIRED.value,
        )
    )
    runtime_profile = RuntimeProfile(
        _parse_enum_value(
            values,
            RUNTIME_PROFILE_ENV_VAR,
            RuntimeProfile,
            RuntimeProfile.PRODUCTION.value,
        )
    )

    return RuntimeSettings(
        authentication_mode=authentication_mode,
        runtime_profile=runtime_profile,
        api_token=get_api_token(values),
    )

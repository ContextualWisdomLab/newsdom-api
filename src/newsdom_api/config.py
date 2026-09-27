"""Bootstrap configuration for the standalone NewsDOM sidecar service.

Environment variables are accepted only as startup transport into a bounded,
process-local credential registry. Request handling reads the registry rather
than the mutable process environment. Deployments rotate the bearer secret by
restarting the sidecar with a newly injected value.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

# Environment variable holding the shared bearer secret for ``/parse``.
API_TOKEN_ENV_VAR = "NEWSDOM_API_TOKEN"
ALLOW_ANONYMOUS_ENV_VAR = "NEWSDOM_ALLOW_ANONYMOUS"
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


@dataclass(frozen=True, slots=True)
class _RuntimeConfig:
    """Validated settings held by the process-local credential registry."""

    api_token: str | None = None
    allow_anonymous: bool = False


_runtime_config = _RuntimeConfig()


def bootstrap_runtime_config(environ: Mapping[str, str] | None = None) -> None:
    """Replace the runtime registry from an explicit startup environment.

    ``environ`` exists for deterministic bootstrap tests. Production startup
    passes no mapping and snapshots :data:`os.environ` exactly once.
    """

    source = os.environ if environ is None else environ
    raw_token = source.get(API_TOKEN_ENV_VAR)
    token = raw_token.strip() if raw_token is not None else ""
    raw_allow_anonymous = source.get(ALLOW_ANONYMOUS_ENV_VAR, "")

    global _runtime_config
    _runtime_config = _RuntimeConfig(
        api_token=token or None,
        allow_anonymous=raw_allow_anonymous.strip().lower() in _TRUE_VALUES,
    )


def get_api_token() -> str | None:
    """Return the configured ``/parse`` bearer token, or ``None`` when unset.

    Any surrounding whitespace is stripped so an accidentally quoted or
    newline-terminated secret does not silently disable auth comparison.
    """

    return _runtime_config.api_token


def allow_anonymous() -> bool:
    """Return whether an explicit local-development anonymous opt-in exists."""

    return _runtime_config.allow_anonymous

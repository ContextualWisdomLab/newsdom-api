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


@dataclass(frozen=True, slots=True)
class _RuntimeConfig:
    """Validated settings held by the process-local credential registry."""

    api_token: str | None = None


_runtime_config = _RuntimeConfig()


def bootstrap_runtime_config(environ: Mapping[str, str] | None = None) -> None:
    """Replace the registry from an explicit startup environment snapshot.

    ``environ`` is injectable for deterministic tests. Production startup
    calls this without an argument exactly once during module initialization.
    """

    source = os.environ if environ is None else environ
    raw_token = source.get(API_TOKEN_ENV_VAR)
    token = raw_token.strip() if raw_token is not None else ""

    global _runtime_config
    _runtime_config = _RuntimeConfig(api_token=token or None)


def get_api_token() -> str | None:
    """Return the configured bearer token from the startup registry."""

    return _runtime_config.api_token


bootstrap_runtime_config()

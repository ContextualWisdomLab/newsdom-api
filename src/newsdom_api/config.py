"""Bootstrap configuration for the standalone NewsDOM sidecar service.

This module reads the leaf service's *own* runtime settings from the process
environment. It is deliberately minimal: the environment is used only as a
bootstrap transport for the sidecar's own configuration (mirroring how
``NEWSDOM_MINERU_BIN`` is resolved in :mod:`newsdom_api.mineru_runner`). No
secret is hardcoded, and values are evaluated on each call so deployments can
rotate them without a process restart.
"""

from __future__ import annotations

import os

# Environment variable holding the shared bearer secret for ``/parse``.
API_TOKEN_ENV_VAR = "NEWSDOM_API_TOKEN"
ALLOW_ANONYMOUS_ENV_VAR = "NEWSDOM_ALLOW_ANONYMOUS"
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def get_api_token() -> str | None:
    """Return the configured ``/parse`` bearer token, or ``None`` when unset.

    Any surrounding whitespace is stripped so an accidentally quoted or
    newline-terminated secret does not silently disable auth comparison.
    """

    raw = os.environ.get(API_TOKEN_ENV_VAR)
    if raw is None:
        return None
    token = raw.strip()
    return token or None


def allow_anonymous() -> bool:
    """Return whether an explicit local-development anonymous opt-in exists."""

    return (
        os.environ.get(ALLOW_ANONYMOUS_ENV_VAR, "").strip().lower()
        in _TRUE_VALUES
    )

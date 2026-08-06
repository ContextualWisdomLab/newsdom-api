"""Contracts for process-local parser admission control."""

import json
from typing import Awaitable, Callable

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import create_app, security_boundary_middleware


def _development_settings(*, capacity: int) -> RuntimeSettings:
    """Return explicit development settings for one admission-control test."""

    return RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
        max_concurrent_parses=capacity,
    )


def _parse_request(application: FastAPI) -> Request:
    """Build a body-hostile parse request for direct middleware verification."""

    async def receive() -> dict[str, object]:
        raise AssertionError("saturated admission must not read the request body")

    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/parse",
            "raw_path": b"/parse",
            "query_string": b"",
            "headers": [],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "root_path": "",
            "app": application,
        },
        receive,
    )


def test_application_binds_configured_process_local_parse_capacity() -> None:
    """Each application should own the immutable parse capacity it was given."""

    application = create_app(
        _development_settings(capacity=3),
        runtime_readiness_probe=lambda: True,
    )

    assert application.state.parse_admission_limiter.capacity == 3


def test_limiter_rejects_excess_work_without_waiting_and_recovers() -> None:
    """One released lease should immediately restore one unit of capacity."""

    application = create_app(
        _development_settings(capacity=1),
        runtime_readiness_probe=lambda: True,
    )
    limiter = application.state.parse_admission_limiter

    assert limiter.try_acquire() is True
    assert limiter.try_acquire() is False

    limiter.release()

    assert limiter.try_acquire() is True
    limiter.release()


@pytest.mark.asyncio
async def test_saturation_returns_fixed_429_before_downstream_or_body_work() -> None:
    """Excess parser work should fail before multipart or parser execution."""

    application = create_app(
        _development_settings(capacity=1),
        runtime_readiness_probe=lambda: True,
    )
    limiter = application.state.parse_admission_limiter
    assert limiter.try_acquire() is True
    downstream_called = False

    async def downstream(_request: Request) -> Response:
        nonlocal downstream_called
        downstream_called = True
        return JSONResponse({"status": "unexpected"})

    response = await security_boundary_middleware(
        _parse_request(application),
        downstream,
    )

    assert response.status_code == 429
    assert json.loads(response.body) == {"detail": "Too Many Requests"}
    assert response.headers["Retry-After"] == "1"
    assert response.headers["Cache-Control"] == "no-store, no-cache, max-age=0"
    assert downstream_called is False
    limiter.release()

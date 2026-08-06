"""Contracts for process-local parser admission control."""

import asyncio
import json

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


def _production_settings(*, capacity: int) -> RuntimeSettings:
    """Return fail-closed production settings with one fixed parser token."""

    return RuntimeSettings(
        authentication_mode=AuthenticationMode.REQUIRED,
        runtime_profile=RuntimeProfile.PRODUCTION,
        api_token="admission-test-token",
        max_concurrent_parses=capacity,
    )


def _parse_request(
    application: FastAPI,
    *,
    headers: list[tuple[bytes, bytes]] | None = None,
) -> Request:
    """Build a body-hostile parse request for direct middleware verification."""

    async def receive() -> dict[str, object]:
        raise AssertionError("admission middleware must not read the request body")

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
            "headers": headers or [],
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


def test_applications_do_not_share_parser_leases() -> None:
    """One saturated application must not reduce another application's capacity."""

    first = create_app(
        _development_settings(capacity=1),
        runtime_readiness_probe=lambda: True,
    )
    second = create_app(
        _development_settings(capacity=1),
        runtime_readiness_probe=lambda: True,
    )

    assert first.state.parse_admission_limiter.try_acquire() is True
    assert first.state.parse_admission_limiter.try_acquire() is False
    assert second.state.parse_admission_limiter.try_acquire() is True

    first.state.parse_admission_limiter.release()
    second.state.parse_admission_limiter.release()


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


@pytest.mark.asyncio
async def test_successful_downstream_work_returns_its_parser_lease() -> None:
    """A completed parser request should make its lease immediately reusable."""

    application = create_app(
        _development_settings(capacity=1),
        runtime_readiness_probe=lambda: True,
    )
    limiter = application.state.parse_admission_limiter

    async def downstream(_request: Request) -> Response:
        return JSONResponse({"status": "complete"})

    response = await security_boundary_middleware(
        _parse_request(application),
        downstream,
    )

    assert response.status_code == 200
    assert limiter.try_acquire() is True
    limiter.release()


@pytest.mark.asyncio
async def test_exceptional_downstream_work_returns_its_parser_lease() -> None:
    """A parser exception must not permanently consume process capacity."""

    application = create_app(
        _development_settings(capacity=1),
        runtime_readiness_probe=lambda: True,
    )
    limiter = application.state.parse_admission_limiter

    async def downstream(_request: Request) -> Response:
        raise RuntimeError("parser failed")

    with pytest.raises(RuntimeError, match="parser failed"):
        await security_boundary_middleware(
            _parse_request(application),
            downstream,
        )

    assert limiter.try_acquire() is True
    limiter.release()


@pytest.mark.asyncio
async def test_cancelled_downstream_work_returns_its_parser_lease() -> None:
    """Request cancellation must not leak a parser lease."""

    application = create_app(
        _development_settings(capacity=1),
        runtime_readiness_probe=lambda: True,
    )
    limiter = application.state.parse_admission_limiter

    async def downstream(_request: Request) -> Response:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await security_boundary_middleware(
            _parse_request(application),
            downstream,
        )

    assert limiter.try_acquire() is True
    limiter.release()


@pytest.mark.asyncio
async def test_authentication_failure_does_not_consume_parser_capacity() -> None:
    """Unauthorized requests should be rejected before admission accounting."""

    application = create_app(
        _production_settings(capacity=2),
        runtime_readiness_probe=lambda: True,
    )
    downstream_called = False

    async def downstream(_request: Request) -> Response:
        nonlocal downstream_called
        downstream_called = True
        return JSONResponse({"status": "unexpected"})

    response = await security_boundary_middleware(
        _parse_request(application),
        downstream,
    )
    limiter = application.state.parse_admission_limiter

    assert response.status_code == 401
    assert downstream_called is False
    assert limiter.try_acquire() is True
    assert limiter.try_acquire() is True
    assert limiter.try_acquire() is False
    limiter.release()
    limiter.release()


@pytest.mark.asyncio
async def test_thirty_two_requests_observe_a_four_request_capacity_bound() -> None:
    """A realistic burst should admit four requests and reject the other 28."""

    capacity = 4
    application = create_app(
        _development_settings(capacity=capacity),
        runtime_readiness_probe=lambda: True,
    )
    all_admitted = asyncio.Event()
    release_admitted = asyncio.Event()
    admitted_count = 0

    async def held_downstream(_request: Request) -> Response:
        nonlocal admitted_count
        admitted_count += 1
        if admitted_count == capacity:
            all_admitted.set()
        await release_admitted.wait()
        return JSONResponse({"status": "complete"})

    async def unexpected_downstream(_request: Request) -> Response:
        raise AssertionError("saturated requests must not reach downstream parsing")

    admitted_tasks = [
        asyncio.create_task(
            security_boundary_middleware(
                _parse_request(application),
                held_downstream,
            )
        )
        for _ in range(capacity)
    ]
    await asyncio.wait_for(all_admitted.wait(), timeout=1.0)

    saturated_responses = await asyncio.gather(
        *[
            security_boundary_middleware(
                _parse_request(application),
                unexpected_downstream,
            )
            for _ in range(32 - capacity)
        ]
    )

    assert [response.status_code for response in saturated_responses] == [429] * 28
    assert all(response.headers["Retry-After"] == "1" for response in saturated_responses)

    release_admitted.set()
    admitted_responses = await asyncio.gather(*admitted_tasks)

    assert [response.status_code for response in admitted_responses] == [200] * capacity
    limiter = application.state.parse_admission_limiter
    reacquired = [limiter.try_acquire() for _ in range(capacity)]
    assert reacquired == [True] * capacity
    assert limiter.try_acquire() is False
    for _ in range(capacity):
        limiter.release()


def test_openapi_documents_parser_saturation_response() -> None:
    """The parser operation should publish the fixed 429 response contract."""

    application = create_app(
        _development_settings(capacity=1),
        runtime_readiness_probe=lambda: True,
    )

    response_contract = application.openapi()["paths"]["/parse"]["post"]["responses"]

    assert response_contract["429"]["description"] == "Too Many Requests"

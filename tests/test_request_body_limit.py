"""Request-body admission tests that run before multipart parsing."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi.testclient import TestClient
from starlette.types import Message, Receive, Scope, Send

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import (
    MAX_PARSE_REQUEST_BYTES,
    PAYLOAD_TOO_LARGE_DETAIL,
    RequestBodyLimitMiddleware,
    create_app,
)


ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


def _parse_scope(*, headers: list[tuple[bytes, bytes]] | None = None) -> Scope:
    """Build the minimum HTTP scope needed to exercise the admission middleware."""

    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/parse",
        "raw_path": b"/parse",
        "query_string": b"",
        "headers": headers or [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "root_path": "",
    }


def _run_asgi(
    application: ASGIApp,
    scope: Scope,
    request_messages: list[Message],
) -> tuple[list[Message], int]:
    """Execute one bounded ASGI exchange and return responses plus receive count."""

    responses: list[Message] = []
    receive_count = 0
    messages = iter(request_messages)

    async def receive() -> Message:
        nonlocal receive_count
        receive_count += 1
        return next(messages)

    async def send(message: Message) -> None:
        responses.append(message)

    asyncio.run(application(scope, receive, send))
    return responses, receive_count


def test_declared_oversize_is_rejected_before_body_read() -> None:
    """A trustworthy oversized Content-Length must fail before receive is called."""

    downstream_calls = 0

    async def downstream(_scope: Scope, _receive: Receive, _send: Send) -> None:
        nonlocal downstream_calls
        downstream_calls += 1

    middleware = RequestBodyLimitMiddleware(
        downstream,
        max_body_bytes=10,
        path="/parse",
    )
    responses, receive_count = _run_asgi(
        middleware,
        _parse_scope(headers=[(b"content-length", b"11")]),
        [{"type": "http.request", "body": b"", "more_body": False}],
    )

    assert receive_count == 0
    assert downstream_calls == 0
    assert responses[0]["type"] == "http.response.start"
    assert responses[0]["status"] == 413
    assert PAYLOAD_TOO_LARGE_DETAIL.encode() in responses[1]["body"]


def test_streamed_oversize_without_content_length_fails_closed() -> None:
    """Chunked or otherwise undeclared bodies must be bounded by bytes received."""

    completed = False

    async def downstream(_scope: Scope, receive: Receive, send: Send) -> None:
        nonlocal completed
        while True:
            message = await receive()
            if not message.get("more_body", False):
                break
        completed = True
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = RequestBodyLimitMiddleware(
        downstream,
        max_body_bytes=5,
        path="/parse",
    )
    responses, receive_count = _run_asgi(
        middleware,
        _parse_scope(),
        [
            {"type": "http.request", "body": b"1234", "more_body": True},
            {"type": "http.request", "body": b"56", "more_body": False},
        ],
    )

    assert receive_count == 2
    assert completed is False
    assert responses[0]["type"] == "http.response.start"
    assert responses[0]["status"] == 413
    assert PAYLOAD_TOO_LARGE_DETAIL.encode() in responses[1]["body"]


def test_production_parse_limit_runs_inside_security_headers() -> None:
    """The production body budget must reject before parsing and retain API headers."""

    settings = RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT,
        api_token=None,
    )
    application = create_app(settings, runtime_readiness_probe=lambda: True)
    response = TestClient(application).post(
        "/parse",
        content=b"",
        headers={
            "content-type": "multipart/form-data; boundary=request-limit-test",
            "content-length": str(MAX_PARSE_REQUEST_BYTES + 1),
        },
    )

    assert response.status_code == 413
    assert response.json() == {"detail": PAYLOAD_TOO_LARGE_DETAIL}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'none'" in response.headers["content-security-policy"]

"""Deterministic ASGI tests for request-body admission before multipart parsing."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

import pytest
from starlette.types import Message, Receive, Scope, Send

from newsdom_api.body_limit import (
    RequestBodyLimitMiddleware,
    RequestBodyTooLarge,
    _declared_content_length,
)

ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


def _http_scope(
    *,
    path: str = "/parse",
    method: str = "POST",
    headers: list[tuple[bytes, bytes]] | None = None,
) -> Scope:
    """Build the minimal HTTP scope required by the admission middleware."""

    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "root_path": "",
        "headers": headers or [],
        "client": ("testclient", 1234),
        "server": ("testserver", 80),
    }


async def _run_asgi(
    app: ASGIApp,
    scope: Scope,
    request_messages: list[Message],
) -> list[Message]:
    """Run one ASGI exchange and return every response event."""

    pending = list(request_messages)
    sent: list[Message] = []

    async def receive() -> Message:
        if pending:
            return pending.pop(0)
        return {"type": "http.disconnect"}

    async def send(message: Message) -> None:
        sent.append(message)

    await app(scope, receive, send)
    return sent


class _BodyConsumer:
    """Test ASGI app that consumes the complete request body before responding."""

    def __init__(self) -> None:
        self.calls = 0
        self.body = b""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Consume request chunks and emit a minimal successful response."""

        self.calls += 1
        while True:
            message = await receive()
            if message["type"] != "http.request":
                break
            self.body += message.get("body", b"")
            if not message.get("more_body", False):
                break
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})


def _status(messages: list[Message]) -> int:
    """Return the HTTP status from one ASGI response event sequence."""

    return next(
        message["status"]
        for message in messages
        if message["type"] == "http.response.start"
    )


def _response_json(messages: list[Message]) -> dict[str, str]:
    """Decode the accumulated ASGI response body as JSON."""

    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return json.loads(body)


def test_declared_content_length_requires_one_valid_non_negative_value() -> None:
    """Treat malformed, negative, or duplicated lengths only as unusable hints."""

    assert _declared_content_length(_http_scope(headers=[(b"content-length", b"5")])) == 5
    assert _declared_content_length(_http_scope(headers=[(b"content-length", b"-1")])) is None
    assert _declared_content_length(_http_scope(headers=[(b"content-length", b"nope")])) is None
    assert (
        _declared_content_length(
            _http_scope(
                headers=[(b"content-length", b"5"), (b"Content-Length", b"5")]
            )
        )
        is None
    )


def test_negative_body_limit_is_rejected_at_configuration_time() -> None:
    """Reject invalid limits before the middleware can enter the request path."""

    with pytest.raises(ValueError, match="non-negative"):
        RequestBodyLimitMiddleware(_BodyConsumer(), max_body_size=-1, path="/parse")


@pytest.mark.asyncio
async def test_declared_oversize_is_rejected_without_calling_downstream() -> None:
    """Use Content-Length for safe early rejection before parser allocation."""

    downstream = _BodyConsumer()
    middleware = RequestBodyLimitMiddleware(downstream, max_body_size=5, path="/parse")
    messages = await _run_asgi(
        middleware,
        _http_scope(headers=[(b"content-length", b"6")]),
        [{"type": "http.request", "body": b"123456", "more_body": False}],
    )

    assert downstream.calls == 0
    assert _status(messages) == 413
    assert _response_json(messages) == {"detail": "Payload Too Large"}


@pytest.mark.asyncio
async def test_actual_bytes_reject_understated_content_length() -> None:
    """Count ASGI bytes so an understated header cannot bypass the admission cap."""

    downstream = _BodyConsumer()
    middleware = RequestBodyLimitMiddleware(downstream, max_body_size=5, path="/parse")
    messages = await _run_asgi(
        middleware,
        _http_scope(headers=[(b"content-length", b"1")]),
        [
            {"type": "http.request", "body": b"1234", "more_body": True},
            {"type": "http.request", "body": b"56", "more_body": False},
        ],
    )

    assert downstream.calls == 1
    assert downstream.body == b"1234"
    assert _status(messages) == 413
    assert _response_json(messages) == {"detail": "Payload Too Large"}


@pytest.mark.asyncio
async def test_exact_limit_passes_and_preserves_request_bytes() -> None:
    """Admit an exact-limit body without changing downstream receive semantics."""

    downstream = _BodyConsumer()
    middleware = RequestBodyLimitMiddleware(downstream, max_body_size=5, path="/parse")
    messages = await _run_asgi(
        middleware,
        _http_scope(headers=[(b"content-length", b"invalid")]),
        [
            {"type": "http.request", "body": b"12", "more_body": True},
            {"type": "http.request", "body": b"345", "more_body": False},
        ],
    )

    assert downstream.calls == 1
    assert downstream.body == b"12345"
    assert _status(messages) == 204


@pytest.mark.asyncio
async def test_unselected_route_bypasses_body_admission() -> None:
    """Keep the compatibility boundary scoped to the parser upload route only."""

    downstream = _BodyConsumer()
    middleware = RequestBodyLimitMiddleware(downstream, max_body_size=1, path="/parse")
    messages = await _run_asgi(
        middleware,
        _http_scope(path="/health", method="GET", headers=[(b"content-length", b"6")]),
        [{"type": "http.request", "body": b"123456", "more_body": False}],
    )

    assert downstream.calls == 1
    assert downstream.body == b"123456"
    assert _status(messages) == 204


@pytest.mark.asyncio
async def test_oversize_after_response_start_is_not_rewritten() -> None:
    """Never emit a second status if a nonconforming downstream app already started."""

    async def starts_before_reading(
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await receive()

    middleware = RequestBodyLimitMiddleware(
        starts_before_reading,
        max_body_size=1,
        path="/parse",
    )

    with pytest.raises(RequestBodyTooLarge):
        await _run_asgi(
            middleware,
            _http_scope(),
            [{"type": "http.request", "body": b"12", "more_body": False}],
        )

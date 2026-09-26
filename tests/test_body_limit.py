"""Deterministic ASGI tests for request-body admission before multipart parsing."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Iterator

import httpx
import pytest
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import Message, Receive, Scope, Send

from newsdom_api.body_limit import (
    RequestBodyLimitMiddleware,
    RequestBodyTooLarge,
    _declared_content_length,
    _route_path,
)
from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import MAX_PARSE_REQUEST_BYTES, create_app

ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


def _http_scope(
    *,
    path: str = "/parse",
    method: str = "POST",
    headers: list[tuple[bytes, bytes]] | None = None,
    root_path: str = "",
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
        "root_path": root_path,
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

    assert _declared_content_length(
        _http_scope(headers=[(b"content-length", b"5")])
    ) == 5
    assert (
        _declared_content_length(
            _http_scope(headers=[(b"content-length", b"-1")])
        )
        is None
    )
    assert (
        _declared_content_length(
            _http_scope(headers=[(b"content-length", b"nope")])
        )
        is None
    )
    assert (
        _declared_content_length(
            _http_scope(
                headers=[
                    (b"content-length", b"5"),
                    (b"Content-Length", b"5"),
                ]
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
    middleware = RequestBodyLimitMiddleware(
        downstream,
        max_body_size=5,
        path="/parse",
    )
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
    middleware = RequestBodyLimitMiddleware(
        downstream,
        max_body_size=5,
        path="/parse",
    )
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
    middleware = RequestBodyLimitMiddleware(
        downstream,
        max_body_size=5,
        path="/parse",
    )
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
async def test_disconnect_before_body_is_forwarded() -> None:
    """Preserve non-body receive events on a selected request."""

    downstream = _BodyConsumer()
    middleware = RequestBodyLimitMiddleware(
        downstream,
        max_body_size=5,
        path="/parse",
    )
    messages = await _run_asgi(middleware, _http_scope(), [])

    assert downstream.calls == 1
    assert downstream.body == b""
    assert _status(messages) == 204


@pytest.mark.asyncio
async def test_unselected_route_bypasses_body_admission() -> None:
    """Keep the compatibility boundary scoped to the parser upload route only."""

    downstream = _BodyConsumer()
    middleware = RequestBodyLimitMiddleware(
        downstream,
        max_body_size=1,
        path="/parse",
    )
    messages = await _run_asgi(
        middleware,
        _http_scope(
            path="/health",
            method="GET",
            headers=[(b"content-length", b"6")],
        ),
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


def test_authentication_precedes_parse_body_admission() -> None:
    """Reject unauthenticated parser traffic before body-limit admission runs."""

    application = create_app(
        RuntimeSettings(
            authentication_mode=AuthenticationMode.REQUIRED,
            runtime_profile=RuntimeProfile.PRODUCTION,
            api_token="unit-test-token",
        )
    )
    client = TestClient(application)
    over_limit = str(MAX_PARSE_REQUEST_BYTES + 1)

    unauthorized = client.post(
        "/parse",
        headers={"Content-Length": over_limit},
        content=b"",
    )
    assert unauthorized.status_code == 401
    assert unauthorized.headers["X-Content-Type-Options"] == "nosniff"

    authorized = client.post(
        "/parse",
        headers={
            "Authorization": "Bearer unit-test-token",
            "Content-Length": over_limit,
        },
        content=b"",
    )
    assert authorized.status_code == 413
    assert authorized.json() == {"detail": "Payload Too Large"}
    assert authorized.headers["X-Content-Type-Options"] == "nosniff"
    assert authorized.headers["Cache-Control"] == "no-store, no-cache, max-age=0"


def _authorized_parse_client() -> TestClient:
    """Return a client for the real application with required authentication."""

    application = create_app(
        RuntimeSettings(
            authentication_mode=AuthenticationMode.REQUIRED,
            runtime_profile=RuntimeProfile.PRODUCTION,
            api_token="unit-test-token",
        )
    )
    return TestClient(application)


_MULTIPART_BOUNDARY = "newsdom-body-limit-boundary"


def _oversized_multipart_chunks() -> Iterator[bytes]:
    """Yield a well-formed multipart upload whose file part exceeds the raw cap."""

    yield (
        f"--{_MULTIPART_BOUNDARY}\r\n"
        'Content-Disposition: form-data; name="file"; filename="fixture.pdf"\r\n'
        "Content-Type: application/pdf\r\n\r\n%PDF-"
    ).encode("ascii")
    chunk = b"x" * (1024 * 1024)
    for _ in range(MAX_PARSE_REQUEST_BYTES // len(chunk) + 1):
        yield chunk
    yield f"\r\n--{_MULTIPART_BOUNDARY}--\r\n".encode("ascii")


def _assert_security_headed_413(response: httpx.Response) -> None:
    """Require the sanitized 413 contract inside the security-header boundary."""

    assert response.status_code == 413
    assert response.json() == {"detail": "Payload Too Large"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Content-Security-Policy"] == (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store, no-cache, max-age=0"


def test_real_app_chunked_oversize_without_content_length_is_413() -> None:
    """A chunked upload with no length hint is capped mid-parse as 413, not 400.

    FastAPI wraps non-HTTP exceptions raised while reading form data into a
    generic 400; the limiter's signal must survive that wrapper.
    """

    client = _authorized_parse_client()

    response = client.post(
        "/parse",
        headers={
            "Authorization": "Bearer unit-test-token",
            "Content-Type": f"multipart/form-data; boundary={_MULTIPART_BOUNDARY}",
        },
        content=_oversized_multipart_chunks(),
    )

    assert response.request.headers.get("content-length") is None
    assert response.request.headers["transfer-encoding"] == "chunked"
    _assert_security_headed_413(response)


def test_real_app_understated_content_length_oversize_is_413() -> None:
    """An understated Content-Length cannot smuggle an oversized body past 413."""

    client = _authorized_parse_client()

    response = client.post(
        "/parse",
        headers={
            "Authorization": "Bearer unit-test-token",
            "Content-Type": f"multipart/form-data; boundary={_MULTIPART_BOUNDARY}",
            "Content-Length": "128",
        },
        content=b"".join(_oversized_multipart_chunks()),
    )

    assert response.request.headers["content-length"] == "128"
    _assert_security_headed_413(response)


def test_body_limit_signal_is_a_413_http_exception() -> None:
    """FastAPI re-raises HTTPException from body readers instead of wrapping it."""

    signal = RequestBodyTooLarge()

    assert isinstance(signal, StarletteHTTPException)
    assert signal.status_code == 413
    assert signal.detail == "Payload Too Large"


@pytest.mark.parametrize(
    ("path", "root_path", "expected"),
    [
        ("/parse", "", "/parse"),
        ("/api/parse", "/api", "/parse"),
        ("/parse", "/api", "/parse"),
        ("/api", "/api", ""),
        ("/apiparse", "/api", "/apiparse"),
    ],
)
def test_route_path_strips_root_path_only_at_a_segment_boundary(
    path: str, root_path: str, expected: str
) -> None:
    """Match Starlette's routing view of the path under a proxy prefix or mount."""

    assert _route_path(_http_scope(path=path, root_path=root_path)) == expected


@pytest.mark.asyncio
async def test_root_path_prefixed_parse_route_is_still_bounded() -> None:
    """A proxy `root_path` or mount prefix does not take `/parse` out of scope."""

    downstream = _BodyConsumer()
    middleware = RequestBodyLimitMiddleware(
        downstream,
        max_body_size=4,
        path="/parse",
    )
    messages = await _run_asgi(
        middleware,
        _http_scope(path="/api/parse", root_path="/api"),
        [{"type": "http.request", "body": b"12345", "more_body": False}],
    )

    assert downstream.calls == 1
    assert _status(messages) == 413
    assert _response_json(messages) == {"detail": "Payload Too Large"}

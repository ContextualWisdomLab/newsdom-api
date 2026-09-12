"""ASGI request-body admission limits for parser uploads."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.responses import JSONResponse
from starlette.types import Message, Receive, Scope, Send

ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]
PAYLOAD_TOO_LARGE_DETAIL = "Payload Too Large"


class RequestBodyTooLarge(Exception):
    """Signal that actual ASGI request bytes crossed the configured admission cap."""


def _declared_content_length(scope: Scope) -> int | None:
    """Return one valid non-negative Content-Length value, otherwise no hint."""

    values = [
        value
        for name, value in scope.get("headers", [])
        if name.lower() == b"content-length"
    ]
    if len(values) != 1:
        return None
    try:
        declared = int(values[0])
    except (TypeError, ValueError):
        return None
    return declared if declared >= 0 else None


class RequestBodyLimitMiddleware:
    """Bound raw request bytes for one HTTP method/path before body parsing.

    `Content-Length` is only an early-rejection hint. Enforcement always wraps the
    ASGI receive channel and counts actual bytes, so omitted or understated headers
    cannot bypass the limit. The middleware is intended to sit inside the existing
    authentication boundary and outside FastAPI's multipart parsing for `/parse`.

    Remove this compatibility middleware after the repository adopts Starlette
    1.6+ and its native `max_body_size` / `RequestBodyLimitMiddleware` contract.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        max_body_size: int,
        path: str,
        method: str = "POST",
    ) -> None:
        """Bind an ASGI app to a non-negative byte limit and exact route selector."""

        if max_body_size < 0:
            raise ValueError("max_body_size must be non-negative")
        self.app = app
        self.max_body_size = max_body_size
        self.path = path
        self.method = method.upper()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Reject an oversized selected request before downstream body parsing."""

        if (
            scope["type"] != "http"
            or scope.get("method", "").upper() != self.method
            or scope.get("path") != self.path
        ):
            await self.app(scope, receive, send)
            return

        declared_length = _declared_content_length(scope)
        if declared_length is not None and declared_length > self.max_body_size:
            await self._send_too_large(scope, receive, send)
            return

        received_bytes = 0
        response_started = False

        async def limited_receive() -> Message:
            """Wrap receive to enforce the maximum body size limit."""
            nonlocal received_bytes
            message = await receive()
            if message["type"] == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_body_size:
                    raise RequestBodyTooLarge
            return message

        async def tracking_send(message: Message) -> None:
            """Wrap send to track if a response has already started."""
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except RequestBodyTooLarge:
            if response_started:
                raise
            await self._send_too_large(scope, receive, send)

    @staticmethod
    async def _send_too_large(scope: Scope, receive: Receive, send: Send) -> None:
        """Emit the service's sanitized 413 response through the ASGI interface."""

        response = JSONResponse(
            status_code=413,
            content={"detail": PAYLOAD_TOO_LARGE_DETAIL},
        )
        await response(scope, receive, send)

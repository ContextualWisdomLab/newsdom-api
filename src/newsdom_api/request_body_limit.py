"""ASGI admission control for bounded parser request bodies."""

from __future__ import annotations

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class _RequestBodyTooLarge(Exception):
    """Signal that received body bytes crossed the configured admission budget."""


class ParseRequestBodyLimitMiddleware:
    """Reject oversized `/parse` bodies before multipart parsing can consume them."""

    def __init__(self, app: ASGIApp, *, max_body_size: int, detail: str) -> None:
        if max_body_size < 0:
            raise ValueError("max_body_size must be non-negative")
        self.app = app
        self.max_body_size = max_body_size
        self.detail = detail

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Apply the raw-byte budget to POST `/parse` traffic only."""
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or scope.get("path") != "/parse"
        ):
            await self.app(scope, receive, send)
            return

        content_length = self._content_length(scope)
        if content_length is not None and content_length > self.max_body_size:
            await self._send_too_large(scope, receive, send)
            return

        total_size = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal total_size
            message = await receive()
            if message["type"] == "http.request":
                total_size += len(message.get("body", b""))
                if total_size > self.max_body_size:
                    raise _RequestBodyTooLarge
            return message

        async def tracked_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except _RequestBodyTooLarge:
            if response_started:
                raise
            await self._send_too_large(scope, receive, send)

    @staticmethod
    def _content_length(scope: Scope) -> int | None:
        """Return a valid declared body size, treating malformed values as unknown."""
        raw_value = Headers(scope=scope).get("content-length")
        if raw_value is None:
            return None
        try:
            value = int(raw_value)
        except ValueError:
            return None
        return value if value >= 0 else None

    async def _send_too_large(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Send the service's sanitized 413 response without reading more body bytes."""
        response = JSONResponse(
            status_code=413,
            content={"detail": self.detail},
        )
        await response(scope, receive, send)

import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

MAX_UPLOAD_BYTES = 20 * 1024 * 1024

class ContentLengthLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > MAX_UPLOAD_BYTES:
                    return Response(status_code=413, content='{"detail":"Payload Too Large"}')
            except ValueError:
                return Response(status_code=400, content='{"detail":"Invalid Content-Length"}')
        else:
            if request.method in ("POST", "PUT", "PATCH"):
                # We could also intercept chunked requests by wrapping `request.stream()` but Starlette
                # allows replacing `request.receive`.
                pass

        return await call_next(request)

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
app = FastAPI()

class ContentLengthLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 20 * 1024 * 1024:
            return Response(status_code=413, content='{"detail":"Payload Too Large"}')
        return await call_next(request)

print("test")

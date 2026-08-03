import httpx
from fastapi import FastAPI, Request, File, UploadFile, HTTPException
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse
import starlette.formparsers
from starlette.formparsers import MultiPartParser, FormParser

MAX_BYTES = 100
app = FastAPI()

class MaxBodySizeMiddleware:
    def __init__(self, app, max_size):
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = None
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    content_length = int(value)
                except ValueError:
                    pass

        if content_length is not None and content_length > self.max_size:
            await self._send_413(send)
            return

        body_size = 0
        receive_error = False

        async def receive_with_limit():
            nonlocal body_size, receive_error
            message = await receive()
            if message["type"] == "http.request":
                body_size += len(message.get("body", b""))
                if body_size > self.max_size:
                    receive_error = True
                    return {"type": "http.request", "body": b"", "more_body": False} # truncate
            return message

        await self.app(scope, receive_with_limit, send)

        # If truncated, the handler might return 200 or 400.
        # But we really want to return 413.

    async def _send_413(self, send):
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"detail": "Payload Too Large"}',
        })

app.add_middleware(MaxBodySizeMiddleware, max_size=MAX_BYTES)

@app.post("/")
async def upload(file: UploadFile = File(...)):
    return {"size": getattr(file, "size", 0)}

def run():
    uvicorn.run(app, host="127.0.0.1", port=8017, log_level="error")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)

def generate_chunked():
    yield b"--boundary\r\n"
    yield b"Content-Disposition: form-data; name=\"file\"; filename=\"test.txt\"\r\n"
    yield b"Content-Type: text/plain\r\n\r\n"
    yield b"A" * 150 + b"\r\n"
    yield b"--boundary--\r\n"

resp = httpx.post("http://127.0.0.1:8017/", content=generate_chunked(), headers={"Content-Type": "multipart/form-data; boundary=boundary"})
print("Status:", resp.status_code)
print("Text:", resp.text)

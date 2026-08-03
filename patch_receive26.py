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

class PayloadTooLargeError(Exception):
    pass

@app.exception_handler(PayloadTooLargeError)
async def payload_too_large_handler(request: Request, exc: PayloadTooLargeError):
    return JSONResponse(status_code=413, content={"detail": "Payload Too Large"})

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

        async def receive_with_limit():
            nonlocal body_size
            message = await receive()
            if message["type"] == "http.request":
                body_size += len(message.get("body", b""))
                if body_size > self.max_size:
                    # In order to let the exception handler catch it, we must raise it
                    # But the parser catches Exception and returns 400.
                    # Wait, does it catch Exception?
                    raise PayloadTooLargeError("Payload Too Large")
            return message

        try:
            await self.app(scope, receive_with_limit, send)
        except Exception as e:
            if isinstance(e, PayloadTooLargeError):
                # The app might not have caught it if it was during form parsing.
                # Actually Starlette's FormParser catches Exception and raises MultiPartException?
                pass
            raise

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
    uvicorn.run(app, host="127.0.0.1", port=8018, log_level="error")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)

def generate_chunked():
    yield b"--boundary\r\n"
    yield b"Content-Disposition: form-data; name=\"file\"; filename=\"test.txt\"\r\n"
    yield b"Content-Type: text/plain\r\n\r\n"
    yield b"A" * 150 + b"\r\n"
    yield b"--boundary--\r\n"

resp = httpx.post("http://127.0.0.1:8018/", content=generate_chunked(), headers={"Content-Type": "multipart/form-data; boundary=boundary"})
print("Status:", resp.status_code)
print("Text:", resp.text)

import httpx
from fastapi import FastAPI, Request, File, UploadFile
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse

MAX_BYTES = 100
app = FastAPI()

class MaxBodySizeException(Exception):
    def __init__(self, body_len: int):
        self.body_len = body_len

class MaxBodySizeMiddleware:
    """Middleware to set a max body size limit"""

    def __init__(self, app: FastAPI, max_size: int):
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        body_len = 0

        async def receive_with_limit():
            nonlocal body_len
            message = await receive()
            if message["type"] == "http.request":
                body_len += len(message.get("body", b""))
                if body_len > self.max_size:
                    raise MaxBodySizeException(body_len)
            return message

        try:
            await self.app(scope, receive_with_limit, send)
        except MaxBodySizeException:
            # We can't cleanly send a 413 response from here if the app already started sending response headers
            # However, if we fail early before the app sends anything, we could construct a raw ASGI 413 response.
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
    uvicorn.run(app, host="127.0.0.1", port=8007, log_level="error")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)

def generate_chunked():
    yield b"--boundary\r\n"
    yield b"Content-Disposition: form-data; name=\"file\"; filename=\"test.txt\"\r\n"
    yield b"Content-Type: text/plain\r\n\r\n"
    yield b"A" * 150 + b"\r\n"
    yield b"--boundary--\r\n"

resp = httpx.post("http://127.0.0.1:8007/", content=generate_chunked(), headers={"Content-Type": "multipart/form-data; boundary=boundary"})
print("Status:", resp.status_code)
print("Text:", resp.text)

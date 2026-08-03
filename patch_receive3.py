import httpx
from fastapi import FastAPI, Request, File, UploadFile
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse

MAX_BYTES = 100
app = FastAPI()

from starlette.requests import ClientDisconnect

class PayloadTooLargeError(Exception):
    pass

@app.exception_handler(PayloadTooLargeError)
async def payload_too_large_handler(request: Request, exc: PayloadTooLargeError):
    return JSONResponse(status_code=413, content={"detail": "Payload Too Large"})

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Payload Too Large"})

    receive_ = request.receive
    bytes_received = 0

    async def bounded_receive():
        nonlocal bytes_received
        message = await receive_()
        if message["type"] == "http.request":
            bytes_received += len(message.get("body", b""))
            if bytes_received > MAX_BYTES:
                # Tell Starlette parser that client disconnected, it will raise ClientDisconnect
                return {"type": "http.disconnect"}
        return message

    request._receive = bounded_receive

    try:
        return await call_next(request)
    except ClientDisconnect:
        if bytes_received > MAX_BYTES:
            return JSONResponse(status_code=413, content={"detail": "Payload Too Large"})
        raise

@app.post("/")
async def upload(file: UploadFile = File(...)):
    return {"size": getattr(file, "size", 0)}

def run():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)

def generate_chunked():
    yield b"--boundary\r\n"
    yield b"Content-Disposition: form-data; name=\"file\"; filename=\"test.txt\"\r\n"
    yield b"Content-Type: text/plain\r\n\r\n"
    yield b"A" * 150 + b"\r\n"
    yield b"--boundary--\r\n"

resp = httpx.post("http://127.0.0.1:8002/", content=generate_chunked(), headers={"Content-Type": "multipart/form-data; boundary=boundary"})
print("Status:", resp.status_code)
print("Text:", resp.text)

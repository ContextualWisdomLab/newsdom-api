import httpx
from fastapi import FastAPI, Request, File, UploadFile, HTTPException
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse
from starlette.formparsers import MultiPartParser
import starlette.formparsers

MAX_BYTES = 100
app = FastAPI()

# Monkeypatch MultiPartParser.parse
original_parse = MultiPartParser.parse

async def custom_parse(self):
    from starlette.exceptions import HTTPException

    # Check max multipart size dynamically
    # Wait, where is request.headers? self has headers
    # `self` is a FormParser instance which actually has `self.headers` and `self.stream`

    bytes_received = 0
    original_stream = self.stream

    async def bounded_stream():
        nonlocal bytes_received
        async for chunk in original_stream:
            bytes_received += len(chunk)
            if bytes_received > MAX_BYTES:
                raise HTTPException(status_code=413, detail="Payload Too Large")
            yield chunk

    self.stream = bounded_stream()
    return await original_parse(self)

MultiPartParser.parse = custom_parse

@app.post("/")
async def upload(file: UploadFile = File(...)):
    return {"size": getattr(file, "size", 0)}

def run():
    uvicorn.run(app, host="127.0.0.1", port=8021, log_level="error")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)

def generate_chunked():
    yield b"--boundary\r\n"
    yield b"Content-Disposition: form-data; name=\"file\"; filename=\"test.txt\"\r\n"
    yield b"Content-Type: text/plain\r\n\r\n"
    yield b"A" * 150 + b"\r\n"
    yield b"--boundary--\r\n"

resp = httpx.post("http://127.0.0.1:8021/", content=generate_chunked(), headers={"Content-Type": "multipart/form-data; boundary=boundary"})
print("Status:", resp.status_code)
print("Text:", resp.text)

import httpx
from fastapi import FastAPI, Request, File, UploadFile, HTTPException
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse
import starlette.formparsers
from starlette.formparsers import MultiPartParser

app = FastAPI()
# Testing with MAX_PARSE_UPLOAD_BYTES
MAX_PARSE_UPLOAD_BYTES = 20 * 1024 * 1024

original_parse = MultiPartParser.parse

async def custom_parse(self):
    bytes_received = 0
    original_stream = self.stream

    async def bounded_stream():
        nonlocal bytes_received
        async for chunk in original_stream:
            bytes_received += len(chunk)
            if bytes_received > MAX_PARSE_UPLOAD_BYTES:
                from starlette.exceptions import HTTPException
                raise HTTPException(status_code=413, detail="Payload Too Large")
            yield chunk

    self.stream = bounded_stream()
    return await original_parse(self)

MultiPartParser.parse = custom_parse

@app.post("/")
async def upload(file: UploadFile = File(...)):
    return {"size": getattr(file, "size", 0)}

def run():
    uvicorn.run(app, host="127.0.0.1", port=8022, log_level="error")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)

def generate_chunked():
    yield b"--boundary\r\n"
    yield b"Content-Disposition: form-data; name=\"file\"; filename=\"test.txt\"\r\n"
    yield b"Content-Type: text/plain\r\n\r\n"
    yield b"A" * 150 + b"\r\n"
    yield b"--boundary--\r\n"

resp = httpx.post("http://127.0.0.1:8022/", content=generate_chunked(), headers={"Content-Type": "multipart/form-data; boundary=boundary"})
print("Status:", resp.status_code)
print("Text:", resp.text)

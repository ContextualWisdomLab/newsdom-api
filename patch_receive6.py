import httpx
from fastapi import FastAPI, Request, File, UploadFile
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse
from starlette.requests import ClientDisconnect

MAX_BYTES = 100
app = FastAPI()

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Payload Too Large"})
    return await call_next(request)

from starlette.formparsers import MultiPartParser
MultiPartParser.max_file_size = MAX_BYTES
MultiPartParser.max_part_size = MAX_BYTES

@app.post("/")
async def upload(file: UploadFile = File(...)):
    return {"size": getattr(file, "size", 0)}

def run():
    uvicorn.run(app, host="127.0.0.1", port=8005, log_level="error")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)

def generate_chunked():
    yield b"--boundary\r\n"
    yield b"Content-Disposition: form-data; name=\"file\"; filename=\"test.txt\"\r\n"
    yield b"Content-Type: text/plain\r\n\r\n"
    yield b"A" * 150 + b"\r\n"
    yield b"--boundary--\r\n"

resp = httpx.post("http://127.0.0.1:8005/", content=generate_chunked(), headers={"Content-Type": "multipart/form-data; boundary=boundary"})
print("Status:", resp.status_code)
print("Text:", resp.text)

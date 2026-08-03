import httpx
from fastapi import FastAPI, Request, File, UploadFile
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse

app = FastAPI()

import starlette.formparsers
original_parse = starlette.formparsers.MultiPartParser.parse

async def custom_parse(self):
    print("Called parse")
    # wrap self.stream
    original_stream = self.stream
    bytes_received = 0
    async def bounded_stream():
        nonlocal bytes_received
        async for chunk in original_stream:
            bytes_received += len(chunk)
            if bytes_received > 100:
                raise ValueError("Payload Too Large")
            yield chunk

    self.stream = bounded_stream()
    try:
        return await original_parse(self)
    except ValueError as e:
        if str(e) == "Payload Too Large":
            # Need to throw an HTTP Exception
            from starlette.exceptions import HTTPException
            raise HTTPException(status_code=413, detail="Payload Too Large")
        raise

starlette.formparsers.MultiPartParser.parse = custom_parse

@app.post("/")
async def upload(file: UploadFile = File(...)):
    return {"size": getattr(file, "size", 0)}

def run():
    uvicorn.run(app, host="127.0.0.1", port=8014, log_level="error")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)

def generate_chunked():
    yield b"--boundary\r\n"
    yield b"Content-Disposition: form-data; name=\"file\"; filename=\"test.txt\"\r\n"
    yield b"Content-Type: text/plain\r\n\r\n"
    yield b"A" * 150 + b"\r\n"
    yield b"--boundary--\r\n"

resp = httpx.post("http://127.0.0.1:8014/", content=generate_chunked(), headers={"Content-Type": "multipart/form-data; boundary=boundary"})
print("Status:", resp.status_code)
print("Text:", resp.text)

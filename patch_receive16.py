import httpx
from fastapi import FastAPI, Request, File, UploadFile
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse

app = FastAPI()

import starlette.formparsers
original_init = starlette.formparsers.MultiPartParser.__init__

def custom_init(self, headers, stream, **kwargs):
    kwargs["max_files"] = 5
    kwargs["max_fields"] = 5
    original_init(self, headers, stream, **kwargs)

starlette.formparsers.MultiPartParser.__init__ = custom_init

@app.post("/")
async def upload(request: Request):
    try:
        form = await request.form()
        return {"size": getattr(form["file"], "size", 0)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=413, content={"detail": str(e)})

def run():
    uvicorn.run(app, host="127.0.0.1", port=8012, log_level="error")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)

def generate_chunked():
    yield b"--boundary\r\n"
    yield b"Content-Disposition: form-data; name=\"file\"; filename=\"test.txt\"\r\n"
    yield b"Content-Type: text/plain\r\n\r\n"
    yield b"A" * 150 + b"\r\n"
    yield b"--boundary--\r\n"

resp = httpx.post("http://127.0.0.1:8012/", content=generate_chunked(), headers={"Content-Type": "multipart/form-data; boundary=boundary"})
print("Status:", resp.status_code)
print("Text:", resp.text)

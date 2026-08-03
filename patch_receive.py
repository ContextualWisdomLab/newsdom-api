import asyncio
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.testclient import TestClient

MAX_BYTES = 5

app = FastAPI()

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BYTES:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=413, content={"detail": "Payload Too Large"})

    # Check chunked
    if request.headers.get("transfer-encoding") == "chunked" or not content_length:
        receive_ = request.receive
        bytes_received = 0

        async def bounded_receive():
            nonlocal bytes_received
            message = await receive_()
            if message["type"] == "http.request":
                bytes_received += len(message.get("body", b""))
                if bytes_received > MAX_BYTES:
                    # Cancel the rest? We can just raise an error or send a fake disconnect to the parser.
                    # Or raise an exception, but it might result in a 500.
                    raise RuntimeError("Payload Too Large")
            return message

        request._receive = bounded_receive

    return await call_next(request)

@app.post("/")
async def upload(file: UploadFile = File(...)):
    return {"size": getattr(file, "size", 0)}

client = TestClient(app)
try:
    resp = client.post("/", files={"file": ("test.txt", b"12345678")})
    print(resp.status_code, resp.text)
except Exception as e:
    print(e)

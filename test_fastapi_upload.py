import asyncio
import time
from fastapi import FastAPI, UploadFile, File
from fastapi.testclient import TestClient

app = FastAPI()

@app.post("/upload_8k")
async def upload_8k(file: UploadFile = File(...)):
    bytes_read = 0
    t0 = time.time()
    while chunk := await file.read(8192):
        bytes_read += len(chunk)
    t1 = time.time()
    return {"time": t1 - t0, "bytes": bytes_read}

@app.post("/upload_1m")
async def upload_1m(file: UploadFile = File(...)):
    bytes_read = 0
    t0 = time.time()
    while chunk := await file.read(1024 * 1024):
        bytes_read += len(chunk)
    t1 = time.time()
    return {"time": t1 - t0, "bytes": bytes_read}

client = TestClient(app)

def run_bench():
    data = b'0' * (20 * 1024 * 1024)

    res8k = client.post("/upload_8k", files={"file": ("test.pdf", data, "application/pdf")})
    print("8K chunk time:", res8k.json()["time"])

    res1m = client.post("/upload_1m", files={"file": ("test.pdf", data, "application/pdf")})
    print("1M chunk time:", res1m.json()["time"])

if __name__ == "__main__":
    run_bench()

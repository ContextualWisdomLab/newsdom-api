import httpx
from fastapi import FastAPI, Request, File, UploadFile
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse

MAX_BYTES = 100
app = FastAPI()

import starlette.formparsers
original_parse = starlette.formparsers.MultiPartParser.parse

async def bounded_parse(self, stream, boundary, charset):
    raise ValueError("Payload Too Large")

# This is complicated. Is there a better way to enforce total payload size?
# Let's inspect the `request.stream()` wrapping

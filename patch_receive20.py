import httpx
from fastapi import FastAPI, Request, File, UploadFile
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse

app = FastAPI()

import starlette.formparsers
original_parse = starlette.formparsers.MultiPartParser.parse

async def custom_parse(self, stream, boundary, charset, **kwargs):
    # What does parse() accept?
    pass

import inspect
print(inspect.signature(original_parse))

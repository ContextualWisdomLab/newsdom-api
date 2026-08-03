import httpx
from fastapi import FastAPI, Request, File, UploadFile
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse

MAX_BYTES = 100
app = FastAPI()

import multipart
from starlette.formparsers import MultiPartParser
import starlette.formparsers
print(getattr(starlette.formparsers, "multipart", None))

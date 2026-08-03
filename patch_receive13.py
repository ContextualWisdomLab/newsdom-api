import httpx
from fastapi import FastAPI, Request, File, UploadFile
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse
import multipart

app = FastAPI()

import starlette.formparsers
print(starlette.formparsers.MultiPartParser)
print(hasattr(starlette.formparsers.MultiPartParser, "max_part_size"))

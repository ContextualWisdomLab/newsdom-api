import httpx
from fastapi import FastAPI, Request, File, UploadFile
import uvicorn
import threading
import time
from fastapi.responses import JSONResponse
import starlette.formparsers
print(getattr(starlette.formparsers.MultiPartParser, "max_file_size", None))
print(starlette.formparsers.MultiPartParser.max_part_size)
print(getattr(starlette.formparsers, "multipart", None))

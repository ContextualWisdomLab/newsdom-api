from fastapi import FastAPI, Request, HTTPException
import starlette.formparsers
app = FastAPI()
print(getattr(starlette.formparsers, "multipart", None))

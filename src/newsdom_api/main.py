"""FastAPI entrypoints for the NewsDOM service."""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile

from .errors import MineruIncompleteOutputError, MineruRuntimeUnavailableError
from .schemas import ParseResponse
from .service import parse_pdf_bytes

app = FastAPI(title="NewsDOM API")


@app.get("/health")
def health() -> dict[str, str]:
    """Return a minimal liveness response for health checks."""

    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
async def parse(file: Annotated[UploadFile, File(...)]) -> ParseResponse:
    """Parse an uploaded PDF into the canonical DOM response model."""

    if file.size is not None and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Unsupported media type. Only PDF files are allowed.")

    try:
        pdf_bytes = await file.read()
        if not pdf_bytes.startswith(b"%PDF"):
            raise HTTPException(status_code=415, detail="Invalid file content. Not a valid PDF.")

        return await asyncio.to_thread(
            parse_pdf_bytes, pdf_bytes, filename=file.filename or "upload.pdf"
        )
    except MineruRuntimeUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MineruIncompleteOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

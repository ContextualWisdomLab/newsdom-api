"""FastAPI entrypoints for the NewsDOM service."""

from __future__ import annotations

import asyncio
from typing import Annotated

import re
from fastapi import FastAPI, File, HTTPException, UploadFile

from .errors import MineruIncompleteOutputError, MineruRuntimeUnavailableError
from .schemas import ParseResponse
from .service import parse_pdf_bytes

app = FastAPI(
    title="NewsDOM API",
    description="DOM-style parser API for scanned Japanese newspaper PDFs.",
    version="0.2.0",
)


@app.get(
    "/health",
    summary="Health Check",
    description="Returns a minimal liveness response for deployment health checks.",
)
def health() -> dict[str, str]:
    """Return a minimal liveness response for health checks."""

    return {"status": "ok"}


@app.post(
    "/parse",
    response_model=ParseResponse,
    summary="Parse Newspaper PDF",
    description=(
        "Converts a scanned Japanese newspaper PDF into a canonical JSON DOM "
        "document using MinerU."
    ),
)
async def parse(
    file: Annotated[UploadFile, File(description="The newspaper PDF file to parse.")],
) -> ParseResponse:
    """Parse an uploaded PDF into the canonical DOM response model."""

    media_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if media_type != "application/pdf":
        raise HTTPException(
            status_code=415, detail="Unsupported Media Type: expected application/pdf"
        )

    filename = file.filename or "upload.pdf"
    if not re.match(r"^[a-zA-Z0-9_.-]+\.pdf$", filename, flags=re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        pdf_bytes = await file.read()
        return await asyncio.to_thread(parse_pdf_bytes, pdf_bytes, filename=filename)
    except MineruRuntimeUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MineruIncompleteOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

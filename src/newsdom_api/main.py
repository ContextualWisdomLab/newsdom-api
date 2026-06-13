"""FastAPI entrypoints for the NewsDOM service."""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile

from .errors import MineruIncompleteOutputError, MineruRuntimeUnavailableError
from .schemas import ParseResponse
from .service import parse_pdf_bytes

app = FastAPI(
    title="NewsDOM API",
    description="API for converting MinerU OCR output into canonical NewsDOM JSON for scanned Japanese newspaper PDFs.",
    version="0.2.0",
)


@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    response_description="Successful liveness response",
)
def health() -> dict[str, str]:
    """Return a minimal liveness response for health checks."""

    return {"status": "ok"}


@app.post(
    "/parse",
    response_model=ParseResponse,
    tags=["Parsing"],
    summary="Parse PDF Document",
    response_description="The canonical NewsDOM JSON representation of the PDF document",
)
async def parse(
    file: Annotated[
        UploadFile, File(description="The Japanese newspaper PDF file to parse")
    ],
) -> ParseResponse:
    """Parse an uploaded PDF into the canonical DOM response model."""

    try:
        pdf_bytes = await file.read()
        return await asyncio.to_thread(
            parse_pdf_bytes, pdf_bytes, filename=file.filename or "upload.pdf"
        )
    except MineruRuntimeUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MineruIncompleteOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

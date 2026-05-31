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
    description="DOM-style parser API for scanned Japanese newspaper PDFs. Upload a file to `/parse` to extract the article structure.",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a minimal liveness response for health checks."""

    return {"status": "ok"}


@app.post(
    "/parse",
    response_model=ParseResponse,
    summary="Parse PDF into DOM JSON",
    description="Upload a scanned Japanese newspaper PDF and receive a canonical DOM response model.",
)
async def parse(
    file: Annotated[
        UploadFile,
        File(description="A scanned Japanese newspaper PDF file to parse"),
    ]
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

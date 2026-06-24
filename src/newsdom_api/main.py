"""FastAPI entrypoints for the NewsDOM service."""

from __future__ import annotations

import asyncio
from io import BytesIO
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from pypdf import PdfReader

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


def _validate_pdf_structure(pdf_bytes: bytes) -> None:
    """Reject payloads that are not structurally parseable PDFs."""

    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=415,
            detail="Unsupported Media Type: expected application/pdf",
        )
    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=False)
        if len(reader.pages) < 1:
            raise ValueError("PDF has no pages")
    except Exception as exc:
        raise HTTPException(
            status_code=415,
            detail="Unsupported Media Type: expected application/pdf",
        ) from exc


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

    try:
        header = await file.read(5)
        if header != b"%PDF-":
            raise HTTPException(
                status_code=415,
                detail="Unsupported Media Type: missing PDF magic bytes",
            )
        pdf_bytes = header + await file.read()
        _validate_pdf_structure(pdf_bytes)
        return await asyncio.to_thread(
            parse_pdf_bytes, pdf_bytes, filename=file.filename or "upload.pdf"
        )
    except MineruRuntimeUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MineruIncompleteOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

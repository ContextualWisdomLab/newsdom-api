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
    description="DOM-style parser API for scanned Japanese newspaper PDFs, converting MinerU OCR output into canonical JSON.",
    version="0.2.0",
)


@app.get(
    "/health",
    summary="Liveness check",
    description="Return a minimal liveness response for load balancers and health checks.",
)
def health() -> dict[str, str]:
    """Return a minimal liveness response for health checks."""

    return {"status": "ok"}


@app.post(
    "/parse",
    response_model=ParseResponse,
    summary="Parse PDF document",
    description="Upload a scanned Japanese newspaper PDF to convert it into a structured DOM representation.",
    responses={
        200: {
            "description": "Successfully parsed document",
            "content": {
                "application/json": {
                    "example": {
                        "document_id": "upload",
                        "pages": [],
                        "quality": {"status": "success", "parser": "mineru", "warnings": []}
                    }
                }
            }
        },
        502: {"description": "MinerU processing failed or returned incomplete output"},
        503: {"description": "MinerU runtime or environment is unavailable"},
    }
)
async def parse(
    file: Annotated[UploadFile, File(description="The PDF file to parse")]
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

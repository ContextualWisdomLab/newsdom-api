"""FastAPI entrypoints for the NewsDOM service."""

from __future__ import annotations

import asyncio
from typing import Annotated, Callable

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile

from .errors import MineruIncompleteOutputError, MineruRuntimeUnavailableError
from .schemas import ParseResponse
from .service import parse_pdf_bytes

tags_metadata = [
    {
        "name": "Parser",
        "description": "Core PDF parsing endpoints.",
    },
    {
        "name": "System",
        "description": "Health and deployment diagnostic endpoints.",
    },
]

app = FastAPI(
    title="NewsDOM API",
    description="DOM-style parser API for scanned Japanese newspaper PDFs.",
    version="0.2.0",
    openapi_tags=tags_metadata,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """Inject standard security headers into all API responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    is_https = request.url.scheme == "https" or forwarded_proto.lower() == "https"
    if is_https:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


@app.get(
    "/health",
    summary="Health Check",
    description="Returns a minimal liveness response for deployment health checks.",
    tags=["System"],
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
    tags=["Parser"],
    responses={
        415: {"description": "Unsupported Media Type (Not a PDF)"},
        502: {"description": "MinerU Incomplete Output (Bad Gateway)"},
        503: {"description": "MinerU Runtime Unavailable (Service Unavailable)"},
    },
)
async def parse(
    file: Annotated[UploadFile, File(description="The newspaper PDF file to parse.")],
) -> ParseResponse:
    """Parse an uploaded PDF into the canonical DOM response model."""

    if getattr(file, "size", None) is not None and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413, detail="Payload Too Large: maximum file size is 10MB"
        )

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
        return await asyncio.to_thread(
            parse_pdf_bytes, pdf_bytes, filename=file.filename or "upload.pdf"
        )
    except MineruRuntimeUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MineruIncompleteOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

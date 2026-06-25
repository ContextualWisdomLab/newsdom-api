"""FastAPI entrypoints for the NewsDOM service."""

from __future__ import annotations

import asyncio
from io import BytesIO
from typing import Annotated, Callable

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from pypdf import PdfReader

from .errors import MineruIncompleteOutputError, MineruRuntimeUnavailableError
from .schemas import ParseResponse
from .service import parse_pdf_bytes

MAX_PARSE_UPLOAD_BYTES = 20 * 1024 * 1024
UNSUPPORTED_MEDIA_DETAIL = "Unsupported Media Type"
PAYLOAD_TOO_LARGE_DETAIL = "Payload Too Large"

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
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )
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


def _validate_pdf_structure(pdf_bytes: bytes) -> None:
    """Reject payloads that are not structurally parseable PDFs."""

    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=415,
            detail=UNSUPPORTED_MEDIA_DETAIL,
        )
    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=False)
        if len(reader.pages) < 1:
            raise ValueError("PDF has no pages")
    except Exception as exc:
        raise HTTPException(
            status_code=415,
            detail=UNSUPPORTED_MEDIA_DETAIL,
        ) from exc


@app.post(
    "/parse",
    response_model=ParseResponse,
    summary="Parse Newspaper PDF",
    description=(
        "Converts a scanned Japanese newspaper PDF into a canonical JSON DOM "
        "document using MinerU."
    ),
    responses={
        413: {"description": "Payload Too Large"},
        415: {"description": "Unsupported Media Type"},
        502: {"description": "Bad Gateway"},
        503: {"description": "Service Unavailable"},
    },
    tags=["Parser"],
)
async def parse(
    file: Annotated[UploadFile, File(description="The newspaper PDF file to parse.")],
) -> ParseResponse:
    """Parse an uploaded PDF into the canonical DOM response model."""

    media_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if media_type != "application/pdf":
        raise HTTPException(status_code=415, detail=UNSUPPORTED_MEDIA_DETAIL)

    if file.size is not None and file.size > MAX_PARSE_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=PAYLOAD_TOO_LARGE_DETAIL)

    try:
        header = await file.read(5)
        if header != b"%PDF-":
            raise HTTPException(
                status_code=415,
                detail=UNSUPPORTED_MEDIA_DETAIL,
            )
        body = await file.read(MAX_PARSE_UPLOAD_BYTES - len(header) + 1)
        if len(header) + len(body) > MAX_PARSE_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=PAYLOAD_TOO_LARGE_DETAIL)
        pdf_bytes = header + body
        _validate_pdf_structure(pdf_bytes)
        return await asyncio.to_thread(
            parse_pdf_bytes, pdf_bytes, filename=file.filename or "upload.pdf"
        )
    except MineruRuntimeUnavailableError as exc:
        raise HTTPException(status_code=503, detail="Service Unavailable") from exc
    except MineruIncompleteOutputError as exc:
        raise HTTPException(status_code=502, detail="Bad Gateway") from exc

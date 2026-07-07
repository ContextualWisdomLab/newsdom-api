"""FastAPI entrypoints for the NewsDOM service."""

from __future__ import annotations

import asyncio
import logging
from io import BytesIO
from typing import Annotated, Callable

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .errors import MineruIncompleteOutputError, MineruRuntimeUnavailableError
from .schemas import HealthResponse, ParseResponse
from .service import parse_pdf_bytes

MAX_PARSE_UPLOAD_BYTES = 20 * 1024 * 1024
UNSUPPORTED_MEDIA_DETAIL = "Unsupported Media Type"
PAYLOAD_TOO_LARGE_DETAIL = "Payload Too Large"
LOGGER = logging.getLogger("newsdom_api")

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
    contact={
        "name": "Seongho Bae",
        "url": "https://github.com/Seongho-Bae/newsdom-api",
    },
    license_info={
        "name": "MIT License",
        "identifier": "MIT",
    },
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "syntaxHighlight.theme": "monokai",
        "tryItOutEnabled": True,
    },
)


def _apply_security_headers(response: Response, request: Request) -> Response:
    """Inject standard security headers into an API response."""

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store, max-age=0"
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    is_https = request.url.scheme == "https" or forwarded_proto.lower() == "https"
    if is_https:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """Inject standard security headers into all API responses."""
    response = await call_next(request)
    return _apply_security_headers(response, request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> Response:
    """Return sanitized 500 responses with the standard security headers."""

    LOGGER.error("Unhandled server exception", exc_info=exc)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
    return _apply_security_headers(response, request)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns a minimal liveness response for deployment health checks.",
    tags=["System"],
)
def health() -> HealthResponse:
    """Return a minimal liveness response for health checks."""

    return HealthResponse()


def _validate_pdf_structure(pdf_bytes: bytes) -> None:
    """Reject payloads that are not structurally parseable PDFs."""

    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=415,
            detail=UNSUPPORTED_MEDIA_DETAIL,
        )
    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=True)
        if len(reader.pages) < 1:
            raise ValueError("PDF has no pages")
    except (PdfReadError, RecursionError, ValueError, OverflowError):
        raise HTTPException(
            status_code=415,
            detail=UNSUPPORTED_MEDIA_DETAIL,
        ) from None


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
    file: Annotated[
        UploadFile, File(..., description="The newspaper PDF file to parse.")
    ],
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
    except MineruRuntimeUnavailableError:
        raise HTTPException(status_code=503, detail="Service Unavailable") from None
    except MineruIncompleteOutputError:
        raise HTTPException(status_code=502, detail="Bad Gateway") from None

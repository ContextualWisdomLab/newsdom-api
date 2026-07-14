"""FastAPI entrypoints for the NewsDOM service."""

from __future__ import annotations

import asyncio
import hmac
import logging
import tempfile
from pathlib import Path
from typing import Annotated, Callable

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import JSONResponse
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .config import get_api_token
from .errors import MineruIncompleteOutputError, MineruRuntimeUnavailableError
from .mineru_runner import (
    DEFAULT_LANGUAGE,
    DEFAULT_MODE,
    normalize_language,
    normalize_mode,
)
from .schemas import HealthResponse, ParseResponse
from .service import parse_pdf

MAX_PARSE_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_VALIDATION_PAGES = 1000
UNSUPPORTED_MEDIA_DETAIL = "Unsupported Media Type"
PAYLOAD_TOO_LARGE_DETAIL = "Payload Too Large"
INVALID_PARSE_PARAMS_DETAIL = "Invalid parse parameters"
UNAUTHORIZED_DETAIL = "Unauthorized"
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
    description=(
        "Language-agnostic PDF-to-DOM parser API. Converts a PDF into a "
        "canonical JSON document tree (pages, sections, headings, body blocks, "
        "images, and bounding boxes) using MinerU."
    ),
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
    response.headers["Cache-Control"] = "no-store, no-cache, max-age=0"
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


def require_authorization(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Enforce optional bearer authentication on protected endpoints.

    When the sidecar has a shared secret configured (via
    :func:`newsdom_api.config.get_api_token`), callers must present a matching
    ``Authorization: Bearer <token>`` header; otherwise a ``401`` is raised. If
    no secret is configured the service stays open, which keeps the standalone
    development experience friction-free. The comparison is constant-time.
    """

    token = get_api_token()
    if token is None:
        return
    expected = f"Bearer {token}"
    provided = authorization or ""
    if not hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(
            status_code=401,
            detail=UNAUTHORIZED_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )


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


def _validate_pdf_structure(file_path: Path) -> None:
    """Reject payloads that are not structurally parseable PDFs."""
    with file_path.open("rb") as f:
        magic = f.read(5)
    if magic != b"%PDF-":
        raise HTTPException(
            status_code=415,
            detail=UNSUPPORTED_MEDIA_DETAIL,
        )
    try:
        reader = PdfReader(file_path, strict=True)
        if len(reader.pages) < 1:
            raise ValueError("PDF has no pages")
        if len(reader.pages) > MAX_VALIDATION_PAGES:
            raise HTTPException(
                status_code=413,
                detail=PAYLOAD_TOO_LARGE_DETAIL,
            )
    except (PdfReadError, RecursionError, ValueError, OverflowError):
        raise HTTPException(
            status_code=415,
            detail=UNSUPPORTED_MEDIA_DETAIL,
        ) from None


@app.post(
    "/parse",
    response_model=ParseResponse,
    summary="Parse PDF into a DOM tree",
    description=(
        "Converts a PDF into a canonical JSON DOM document using MinerU. The "
        "optional `language` and `mode` form fields select the MinerU language "
        "family (default `ch`) and parsing mode (`auto`/`ocr`/`txt`, "
        "default `auto`). When a shared secret is configured, an "
        "`Authorization: Bearer <token>` header is required."
    ),
    dependencies=[Depends(require_authorization)],
    responses={
        401: {"description": "Unauthorized"},
        413: {"description": "Payload Too Large"},
        415: {"description": "Unsupported Media Type"},
        422: {"description": "Invalid parse parameters"},
        502: {"description": "Bad Gateway"},
        503: {"description": "Service Unavailable"},
    },
    tags=["Parser"],
)
async def parse(
    file: Annotated[UploadFile, File(..., description="The PDF file to parse.")],
    language: Annotated[
        str,
        Form(
            description=(
                "MinerU language family or compatibility alias (e.g. `ch`, "
                "`en`, `japan`, `korean`, `arabic`, `devanagari`)."
            )
        ),
    ] = DEFAULT_LANGUAGE,
    mode: Annotated[
        str,
        Form(
            description=(
                "MinerU parsing mode: `auto` (born-digital text PDFs skip forced "
                "OCR), `ocr` (force OCR), or `txt` (embedded text layer only)."
            )
        ),
    ] = DEFAULT_MODE,
) -> ParseResponse:
    """Parse an uploaded PDF into the canonical DOM response model."""

    media_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if media_type != "application/pdf":
        raise HTTPException(status_code=415, detail=UNSUPPORTED_MEDIA_DETAIL)

    try:
        resolved_language = normalize_language(language)
        resolved_mode = normalize_mode(mode)
    except ValueError:
        raise HTTPException(
            status_code=422, detail=INVALID_PARSE_PARAMS_DETAIL
        ) from None

    file_size = getattr(file, "size", None)
    if file_size is not None and file_size > MAX_PARSE_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=PAYLOAD_TOO_LARGE_DETAIL)

    tmp_path: Path | None = None
    try:
        header = await file.read(5)
        if header != b"%PDF-":
            raise HTTPException(
                status_code=415,
                detail=UNSUPPORTED_MEDIA_DETAIL,
            )

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            LOGGER.debug("Created temporary upload file %s", tmp_path)
            tmp.write(header)

            bytes_read = len(header)
            while chunk := await file.read(8192):
                bytes_read += len(chunk)
                if bytes_read > MAX_PARSE_UPLOAD_BYTES:
                    LOGGER.warning(
                        "Rejecting upload over limit: %s bytes read", bytes_read
                    )
                    raise HTTPException(
                        status_code=413, detail=PAYLOAD_TOO_LARGE_DETAIL
                    )
                tmp.write(chunk)

        LOGGER.debug("Wrote %s upload bytes to %s", bytes_read, tmp_path)
        await asyncio.to_thread(_validate_pdf_structure, tmp_path)
        return await asyncio.to_thread(
            parse_pdf,
            tmp_path,
            filename=file.filename or "upload.pdf",
            language=resolved_language,
            mode=resolved_mode,
        )

    except MineruRuntimeUnavailableError:
        raise HTTPException(status_code=503, detail="Service Unavailable") from None
    except MineruIncompleteOutputError:
        raise HTTPException(status_code=502, detail="Bad Gateway") from None
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                LOGGER.exception("Failed to remove temporary upload file %s", tmp_path)

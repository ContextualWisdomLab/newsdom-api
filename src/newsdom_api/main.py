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
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .config import (
    AuthenticationMode,
    MAX_BEARER_HEADER_BYTES,
    RuntimeSettings,
    load_runtime_settings,
)
from .errors import MineruIncompleteOutputError, MineruRuntimeUnavailableError
from .mineru_runner import (
    DEFAULT_LANGUAGE,
    DEFAULT_MODE,
    mineru_runtime_available,
    normalize_language,
    normalize_mode,
)
from .schemas import HealthResponse, ParseResponse, ReadinessResponse
from .service import parse_pdf

MAX_PARSE_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_AUTHORIZATION_HEADER_BYTES = MAX_BEARER_HEADER_BYTES
UNSUPPORTED_MEDIA_DETAIL = "Unsupported Media Type"
PAYLOAD_TOO_LARGE_DETAIL = "Payload Too Large"
INVALID_PARSE_PARAMS_DETAIL = "Invalid parse parameters"
UNAUTHORIZED_DETAIL = "Unauthorized"
SERVICE_UNAVAILABLE_DETAIL = "Service Unavailable"
LOGGER = logging.getLogger("newsdom_api")
BEARER_SCHEME = HTTPBearer(auto_error=False, scheme_name="BearerAuth")

tags_metadata = [
    {"name": "Parser", "description": "Core PDF parsing endpoints."},
    {
        "name": "System",
        "description": "Health and deployment diagnostic endpoints.",
    },
]


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


def _runtime_settings(request: Request) -> RuntimeSettings:
    """Return the immutable settings bound to the current application instance."""

    settings = request.app.state.runtime_settings
    if not isinstance(settings, RuntimeSettings):
        raise RuntimeError("Application runtime settings are unavailable")
    return settings


def _authorization_values(request: Request) -> list[bytes]:
    """Return every raw Authorization header without lossy string coercion."""

    return [
        value
        for name, value in request.scope.get("headers", [])
        if name.lower() == b"authorization"
    ]


def _unauthorized_response() -> JSONResponse:
    """Return one fixed caller-authentication failure response."""

    return JSONResponse(
        status_code=401,
        content={"detail": UNAUTHORIZED_DETAIL},
        headers={"WWW-Authenticate": "Bearer"},
    )


def _parse_access_failure(request: Request) -> JSONResponse | None:
    """Validate `/parse` authorization before multipart upload parsing begins."""

    settings = _runtime_settings(request)
    if settings.authentication_mode is AuthenticationMode.DISABLED:
        return None
    token = settings.api_token
    if token is None:
        return JSONResponse(
            status_code=503,
            content={"detail": SERVICE_UNAVAILABLE_DETAIL},
        )

    authorization_values = _authorization_values(request)
    if len(authorization_values) != 1:
        return _unauthorized_response()
    provided = authorization_values[0]
    if len(provided) > MAX_BEARER_HEADER_BYTES:
        return _unauthorized_response()

    expected = f"Bearer {token}".encode("utf-8")
    if not hmac.compare_digest(provided, expected):
        return _unauthorized_response()
    return None


async def security_boundary_middleware(
    request: Request,
    call_next: Callable,
) -> Response:
    """Enforce parser authorization before reading the request body and add headers."""

    if request.method == "POST" and request.scope.get("path") == "/parse":
        failure = _parse_access_failure(request)
        if failure is not None:
            return _apply_security_headers(failure, request)
    response = await call_next(request)
    return _apply_security_headers(response, request)


async def global_exception_handler(request: Request, exc: Exception) -> Response:
    """Return sanitized 500 responses with the standard security headers."""

    LOGGER.error("Unhandled server exception", exc_info=exc)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
    return _apply_security_headers(response, request)


def health() -> HealthResponse:
    """Return a minimal liveness response independent from service readiness."""

    return HealthResponse()


def ready(request: Request) -> ReadinessResponse:
    """Return readiness only when authentication and MinerU runtime are available."""

    settings = _runtime_settings(request)
    runtime_probe = request.app.state.runtime_readiness_probe
    if not settings.authentication_ready or not runtime_probe():
        raise HTTPException(status_code=503, detail=SERVICE_UNAVAILABLE_DETAIL)
    return ReadinessResponse()


def _validate_pdf_structure(file_path: Path) -> None:
    """Reject payloads that are not structurally parseable PDFs."""

    with file_path.open("rb") as file_handle:
        magic = file_handle.read(5)
    if magic != b"%PDF-":
        raise HTTPException(status_code=415, detail=UNSUPPORTED_MEDIA_DETAIL)
    try:
        reader = PdfReader(file_path, strict=True)
        if len(reader.pages) < 1:
            raise ValueError("PDF has no pages")
    except (PdfReadError, RecursionError, ValueError, OverflowError):
        raise HTTPException(
            status_code=415,
            detail=UNSUPPORTED_MEDIA_DETAIL,
        ) from None


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
    """Parse an authorized uploaded PDF into the canonical DOM response model."""

    media_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if media_type != "application/pdf":
        raise HTTPException(status_code=415, detail=UNSUPPORTED_MEDIA_DETAIL)

    try:
        resolved_language = normalize_language(language)
        resolved_mode = normalize_mode(mode)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=INVALID_PARSE_PARAMS_DETAIL,
        ) from None

    file_size = getattr(file, "size", None)
    if file_size is not None and file_size > MAX_PARSE_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=PAYLOAD_TOO_LARGE_DETAIL)

    tmp_path: Path | None = None
    try:
        header = await file.read(5)
        if header != b"%PDF-":
            raise HTTPException(status_code=415, detail=UNSUPPORTED_MEDIA_DETAIL)

        with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
            tmp_path = Path(temporary_file.name)
            LOGGER.debug("Created temporary upload file %s", tmp_path)
            temporary_file.write(header)

            bytes_read = len(header)
            while chunk := await file.read(8192):
                bytes_read += len(chunk)
                if bytes_read > MAX_PARSE_UPLOAD_BYTES:
                    LOGGER.warning(
                        "Rejecting upload over limit: %s bytes read",
                        bytes_read,
                    )
                    raise HTTPException(
                        status_code=413,
                        detail=PAYLOAD_TOO_LARGE_DETAIL,
                    )
                temporary_file.write(chunk)

        LOGGER.debug("Wrote %s upload bytes to %s", bytes_read, tmp_path)
        _validate_pdf_structure(tmp_path)
        return await asyncio.to_thread(
            parse_pdf,
            tmp_path,
            filename=file.filename or "upload.pdf",
            language=resolved_language,
            mode=resolved_mode,
        )
    except MineruRuntimeUnavailableError:
        raise HTTPException(
            status_code=503, detail=SERVICE_UNAVAILABLE_DETAIL
        ) from None
    except MineruIncompleteOutputError:
        raise HTTPException(status_code=502, detail="Bad Gateway") from None
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                LOGGER.exception("Failed to remove temporary upload file %s", tmp_path)


def create_app(
    settings: RuntimeSettings | None = None,
    *,
    runtime_readiness_probe: Callable[[], bool] | None = None,
) -> FastAPI:
    """Create a NewsDOM application with immutable settings and injected readiness."""

    application_settings = settings or load_runtime_settings()
    if application_settings.authentication_mode is AuthenticationMode.DISABLED:
        LOGGER.warning(
            "Parser authentication is disabled for the explicit development profile"
        )
    elif not application_settings.authentication_ready:
        LOGGER.error("Parser authentication configuration is unavailable")

    application = FastAPI(
        title="NewsDOM API",
        description=(
            "Language-agnostic PDF-to-DOM parser API. Converts a PDF into a "
            "canonical JSON document tree using MinerU. Authentication is "
            "required by default; an explicit development-only bypass is available."
        ),
        version="0.2.0",
        contact={
            "name": "Seongho Bae",
            "url": "https://github.com/ContextualWisdomLab/newsdom-api",
        },
        license_info={"name": "MIT License", "identifier": "MIT"},
        openapi_tags=tags_metadata,
        swagger_ui_parameters={
            "displayRequestDuration": True,
            "syntaxHighlight.theme": "monokai",
            "tryItOutEnabled": True,
        },
    )
    application.state.runtime_settings = application_settings
    application.state.runtime_readiness_probe = (
        runtime_readiness_probe or mineru_runtime_available
    )
    application.middleware("http")(security_boundary_middleware)
    application.add_exception_handler(Exception, global_exception_handler)
    application.add_api_route(
        "/health",
        health,
        methods=["GET"],
        response_model=HealthResponse,
        summary="Health Check",
        description="Returns liveness without evaluating traffic readiness.",
        tags=["System"],
    )
    application.add_api_route(
        "/ready",
        ready,
        methods=["GET"],
        response_model=ReadinessResponse,
        summary="Readiness Check",
        description=(
            "Returns ready only when parser authentication configuration and "
            "the MinerU runtime can safely accept traffic."
        ),
        responses={503: {"description": SERVICE_UNAVAILABLE_DETAIL}},
        tags=["System"],
    )
    application.add_api_route(
        "/parse",
        parse,
        methods=["POST"],
        response_model=ParseResponse,
        summary="Parse PDF into a DOM tree",
        description=(
            "Converts an authenticated PDF upload into canonical NewsDOM JSON. "
            "The optional language and mode form fields configure MinerU."
        ),
        dependencies=[Depends(BEARER_SCHEME)],
        responses={
            401: {"description": UNAUTHORIZED_DETAIL},
            413: {"description": PAYLOAD_TOO_LARGE_DETAIL},
            415: {"description": UNSUPPORTED_MEDIA_DETAIL},
            422: {"description": INVALID_PARSE_PARAMS_DETAIL},
            502: {"description": "Bad Gateway"},
            503: {"description": SERVICE_UNAVAILABLE_DETAIL},
        },
        tags=["Parser"],
    )
    return application


app = create_app()

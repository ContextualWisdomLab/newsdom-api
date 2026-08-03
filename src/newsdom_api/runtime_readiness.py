"""Deployment readiness checks for the optional MinerU runtime."""

from __future__ import annotations

import os
import shutil

from fastapi import APIRouter, HTTPException

from .schemas import HealthResponse

MINERU_EXECUTABLE = "mineru"
SERVICE_UNAVAILABLE_DETAIL = "Service Unavailable"

router = APIRouter(tags=["System"])


def is_mineru_runtime_ready() -> bool:
    """Return whether the configured MinerU executable can be invoked.

    ``NEWSDOM_MINERU_BIN`` is evaluated for every probe so runtime deployment
    overrides are reflected immediately. ``shutil.which`` validates both PATH
    commands and explicit executable paths without exposing either value in the
    public readiness response.
    """

    configured = os.environ.get("NEWSDOM_MINERU_BIN")
    executable = configured or MINERU_EXECUTABLE
    return shutil.which(executable) is not None


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Runtime Readiness Check",
    description=(
        "Returns 200 only when the MinerU executable required by `/parse` is "
        "available. Use `/health` for liveness and `/ready` for traffic routing."
    ),
    responses={503: {"description": SERVICE_UNAVAILABLE_DETAIL}},
)
def readiness() -> HealthResponse:
    """Return parser readiness without exposing runtime paths or diagnostics."""

    if not is_mineru_runtime_ready():
        raise HTTPException(status_code=503, detail=SERVICE_UNAVAILABLE_DETAIL)
    return HealthResponse(status="ready")

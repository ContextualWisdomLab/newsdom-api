"""Isolated structural PDF validation with process and resource limits."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import resource
import sys
from enum import Enum
from pathlib import Path
from typing import Final

from pypdf import PdfReader
from pypdf.errors import PdfReadError

LOGGER = logging.getLogger("newsdom_api")

DEFAULT_WALL_CLOCK_SECONDS: Final[float] = 5.0
DEFAULT_CPU_SECONDS: Final[int] = 5
DEFAULT_ADDRESS_SPACE_BYTES: Final[int] = 512 * 1024 * 1024
OUTCOME_KEY: Final[str] = "outcome"
CLIENT_INVALID_EXCEPTIONS: Final[tuple[type[BaseException], ...]] = (
    PdfReadError,
    RecursionError,
    ValueError,
    OverflowError,
    TypeError,
    MemoryError,
)


class ValidationOutcome(str, Enum):
    """Typed child-process result with no path or exception payload."""

    VALID = "valid"
    INVALID_DOCUMENT = "invalid_document"
    VALIDATOR_FAILURE = "validator_failure"


def resource_limits_supported() -> bool:
    """Return whether this platform exposes CPU and address-space limits."""

    return hasattr(resource, "RLIMIT_CPU") and hasattr(resource, "RLIMIT_AS")


def apply_resource_limits(
    *,
    cpu_seconds: int = DEFAULT_CPU_SECONDS,
    address_space_bytes: int = DEFAULT_ADDRESS_SPACE_BYTES,
) -> None:
    """Apply production-supported CPU and address-space limits or raise."""

    if not resource_limits_supported():
        raise RuntimeError("CPU and address-space limits are unavailable")
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    resource.setrlimit(
        resource.RLIMIT_AS, (address_space_bytes, address_space_bytes)
    )


def validate_pdf_structure_in_process(file_path: Path) -> ValidationOutcome:
    """Validate one on-disk PDF after resource limits are already applied."""

    try:
        with file_path.open("rb") as handle:
            magic = handle.read(5)
        if magic != b"%PDF-":
            return ValidationOutcome.INVALID_DOCUMENT
        reader = PdfReader(file_path, strict=True)
        if len(reader.pages) < 1:
            return ValidationOutcome.INVALID_DOCUMENT
        return ValidationOutcome.VALID
    except CLIENT_INVALID_EXCEPTIONS:
        return ValidationOutcome.INVALID_DOCUMENT
    except Exception:
        return ValidationOutcome.VALIDATOR_FAILURE


def decode_child_payload(raw: bytes) -> ValidationOutcome:
    """Parse the child's one-object JSON stdout into a typed outcome."""

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ValidationOutcome.VALIDATOR_FAILURE
    if not isinstance(payload, dict):
        return ValidationOutcome.VALIDATOR_FAILURE
    try:
        return ValidationOutcome(payload.get(OUTCOME_KEY))
    except ValueError:
        return ValidationOutcome.VALIDATOR_FAILURE


def child_main(argv: list[str] | None = None) -> int:
    """Apply limits, validate one path argument, and print one JSON object."""

    args = sys.argv[1:] if argv is None else argv
    try:
        if len(args) != 1:
            raise ValueError("expected one file path")
        apply_resource_limits()
        outcome = validate_pdf_structure_in_process(Path(args[0]))
    except Exception:
        outcome = ValidationOutcome.VALIDATOR_FAILURE
    sys.stdout.write(json.dumps({OUTCOME_KEY: outcome.value}))
    return 0 if outcome is ValidationOutcome.VALID else 1


def _child_pythonpath() -> str:
    """Put the installed `src` tree on the disposable child's import path."""

    src_dir = str(Path(__file__).resolve().parents[1])
    existing = os.environ.get("PYTHONPATH", "")
    if not existing:
        return src_dir
    return src_dir + os.pathsep + existing


async def _reclaim_child(process: asyncio.subprocess.Process) -> None:
    """Terminate a disposable validator child and wait for exit."""

    try:
        process.kill()
        await asyncio.shield(process.wait())
    except Exception:
        LOGGER.exception("Failed to reclaim PDF structural validator child")


async def validate_pdf_structure_isolated(
    file_path: Path,
    *,
    timeout_seconds: float = DEFAULT_WALL_CLOCK_SECONDS,
) -> ValidationOutcome:
    """Run validation in a disposable child and enforce a wall-clock timeout."""

    if not resource_limits_supported():
        LOGGER.error("PDF structural validation cannot apply resource limits")
        return ValidationOutcome.VALIDATOR_FAILURE

    command = (
        sys.executable,
        "-m",
        "newsdom_api.pdf_structure_validator",
        str(file_path),
    )
    child_env = os.environ.copy()
    child_env["PYTHONPATH"] = _child_pythonpath()
    process: asyncio.subprocess.Process | None = None
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=child_env,
        )
        try:
            stdout, _stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
        except asyncio.CancelledError:
            await _reclaim_child(process)
            raise
        except asyncio.TimeoutError:
            await _reclaim_child(process)
            LOGGER.warning("PDF structural validator exceeded wall-clock limit")
            return ValidationOutcome.INVALID_DOCUMENT
        return decode_child_payload(stdout or b"")
    except asyncio.CancelledError:
        raise
    except Exception:
        LOGGER.exception("PDF structural validator failed to launch")
        if process is not None:
            await _reclaim_child(process)
        return ValidationOutcome.VALIDATOR_FAILURE


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(child_main())

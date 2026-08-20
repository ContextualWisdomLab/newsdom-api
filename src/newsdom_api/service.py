"""Service-layer orchestration for temporary-file parsing requests."""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath

from .dom_builder import build_dom
from .mineru_runner import DEFAULT_LANGUAGE, DEFAULT_MODE, run_mineru
from .schemas import ParseResponse


MAX_UPLOAD_FILENAME_LENGTH = 240

# ⚡ Bolt: Pre-compile regex to avoid overhead of compiling on every call
_UNSAFE_UPLOAD_FILENAME_PATTERN = re.compile(r"[^a-zA-Z0-9_.-]")


def _safe_upload_filename(filename: str) -> str:
    """Return a basename for client-supplied upload filenames."""

    # Bound the input to prevent performance degradation/DoS on path parsing and regex
    filename = filename[-512:]
    normalized = filename.replace("\0", "").replace("\\", "/")
    name = PurePosixPath(normalized).name
    name = _UNSAFE_UPLOAD_FILENAME_PATTERN.sub("_", name)
    # ⚡ Bolt: Use .strip("_.") instead of chained .replace() to avoid multiple intermediate string allocations
    if name in ("", ".", "..") or not name.strip("_."):
        return "upload.pdf"
    if len(name) > MAX_UPLOAD_FILENAME_LENGTH:
        suffix = PurePosixPath(name).suffix
        stem_length = MAX_UPLOAD_FILENAME_LENGTH - len(suffix)
        if suffix and stem_length > 0:
            name = f"{PurePosixPath(name).stem[:stem_length]}{suffix}"
        else:
            name = name[:MAX_UPLOAD_FILENAME_LENGTH]
    return name


def parse_pdf(
    file_path: Path,
    filename: str = "upload.pdf",
    *,
    language: str = DEFAULT_LANGUAGE,
    mode: str = DEFAULT_MODE,
) -> ParseResponse:
    """Parse a local PDF file and return the normalized parse result.

    ``language`` and ``mode`` are forwarded to MinerU (see
    :func:`newsdom_api.mineru_runner.run_mineru`) and default to language-agnostic
    automatic detection.
    """

    with tempfile.TemporaryDirectory(prefix="newsdom-upload-") as tempdir:
        safe_name = _safe_upload_filename(filename)
        pdf_path = Path(tempdir) / safe_name
        shutil.copy2(file_path, pdf_path)
        mineru_output = run_mineru(pdf_path, language=language, mode=mode)
        response = build_dom(
            mineru_output["content_list"],
            document_id=pdf_path.stem,
            model=mineru_output.get("model"),
        )
        return response


def parse_pdf_bytes(
    data: bytes,
    filename: str = "upload.pdf",
    *,
    language: str = DEFAULT_LANGUAGE,
    mode: str = DEFAULT_MODE,
) -> ParseResponse:
    """Persist uploaded PDF bytes temporarily and return the normalized parse result.

    ``language`` and ``mode`` are forwarded to :func:`parse_pdf`.
    """

    with tempfile.TemporaryDirectory(prefix="newsdom-upload-") as tempdir:
        pdf_path = Path(tempdir) / "upload.pdf"
        pdf_path.write_bytes(data)
        return parse_pdf(pdf_path, filename, language=language, mode=mode)

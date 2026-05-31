"""Service-layer orchestration for temporary-file parsing requests."""

from __future__ import annotations

import ntpath
import posixpath
import tempfile
from pathlib import Path

from .dom_builder import build_dom
from .mineru_runner import run_mineru
from .schemas import ParseResponse


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename against both POSIX and Windows path separators."""
    name = posixpath.basename(ntpath.basename(filename))
    return name or "upload.pdf"


def parse_pdf_bytes(data: bytes, filename: str = "upload.pdf") -> ParseResponse:
    """Persist uploaded PDF bytes temporarily and return the normalized parse result."""

    with tempfile.TemporaryDirectory(prefix="newsdom-upload-") as tempdir:
        safe_name = _sanitize_filename(filename)
        pdf_path = Path(tempdir) / safe_name
        pdf_path.write_bytes(data)
        mineru_output = run_mineru(pdf_path)
        response = build_dom(
            mineru_output["content_list"],
            document_id=pdf_path.stem,
            model=mineru_output.get("model"),
        )
        return response

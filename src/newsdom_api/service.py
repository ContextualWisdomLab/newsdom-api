"""Service-layer orchestration for temporary-file parsing requests."""

from __future__ import annotations

import tempfile
from pathlib import Path, PurePosixPath

from .dom_builder import build_dom
from .mineru_runner import run_mineru
from .schemas import ParseResponse


def _safe_upload_filename(filename: str) -> str:
    """Return a basename for client-supplied upload filenames."""

    normalized = filename.replace("\0", "").replace("\\", "/")
    name = PurePosixPath(normalized).name
    if name in ("", ".", ".."):
        return "upload.pdf"
    return name[:255]


def parse_pdf_bytes(data: bytes, filename: str = "upload.pdf") -> ParseResponse:
    """Persist uploaded PDF bytes temporarily and return the normalized parse result."""

    with tempfile.TemporaryDirectory(prefix="newsdom-upload-") as tempdir:
        safe_name = _safe_upload_filename(filename)
        pdf_path = Path(tempdir) / safe_name
        pdf_path.write_bytes(data)
        mineru_output = run_mineru(pdf_path)
        response = build_dom(
            mineru_output["content_list"],
            document_id=pdf_path.stem,
            model=mineru_output.get("model"),
        )
        return response

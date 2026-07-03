"""Service-layer orchestration for temporary-file parsing requests."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path, PurePosixPath

from .dom_builder import build_dom
from .mineru_runner import run_mineru
from .schemas import ParseResponse


MAX_UPLOAD_FILENAME_LENGTH = 240


def _safe_upload_filename(filename: str) -> str:
    """Return a basename for client-supplied upload filenames."""

    normalized = filename.replace("\0", "").replace("\\", "/")
    name = PurePosixPath(normalized).name
    name = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
    if name in ("", ".", "..") or not name.replace("_", "").replace(".", ""):
        return "upload.pdf"
    if len(name) > MAX_UPLOAD_FILENAME_LENGTH:
        suffix = PurePosixPath(name).suffix
        stem_length = MAX_UPLOAD_FILENAME_LENGTH - len(suffix)
        if suffix and stem_length > 0:
            name = f"{PurePosixPath(name).stem[:stem_length]}{suffix}"
        else:
            name = name[:MAX_UPLOAD_FILENAME_LENGTH]
    return name


def parse_pdf_file(source_path: Path, filename: str = "upload.pdf") -> ParseResponse:
    """Copy an existing PDF file to a safe temporary location and return the normalized parse result."""

    with tempfile.TemporaryDirectory(prefix="newsdom-upload-") as tempdir:
        safe_name = _safe_upload_filename(filename)
        pdf_path = Path(tempdir) / safe_name
        # Hardlink or copy depending on cross-device filesystem support
        import shutil

        shutil.copy2(source_path, pdf_path)

        mineru_output = run_mineru(pdf_path)
        response = build_dom(
            mineru_output["content_list"],
            document_id=pdf_path.stem,
            model=mineru_output.get("model"),
        )
        return response


def parse_pdf_bytes(data: bytes, filename: str = "upload.pdf") -> ParseResponse:
    """Persist uploaded PDF bytes temporarily and return the normalized parse result."""

    with tempfile.NamedTemporaryFile(delete=False, prefix="newsdom-upload-") as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        return parse_pdf_file(tmp_path, filename=filename)
    finally:
        tmp_path.unlink(missing_ok=True)

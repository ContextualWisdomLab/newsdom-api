"""Regression contracts for PDF structural failure classification."""

from pathlib import Path

import pytest
from fastapi import HTTPException
from pypdf.errors import PdfReadError

from newsdom_api.main import _validate_pdf_structure


@pytest.mark.parametrize(
    "failure",
    [
        PdfReadError("invalid xref table"),
        RecursionError("recursive object graph"),
        ValueError("invalid page structure"),
        OverflowError("oversized parser value"),
        TypeError("invalid parser object type"),
        MemoryError("parser memory exhaustion compatibility case"),
    ],
)
def test_parser_class_failures_are_sanitized_as_415(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: Exception,
) -> None:
    """Known representation/parser failures remain fixed 415 responses."""

    def reject_pdf(_stream: Path, *, strict: bool) -> None:
        assert strict is True
        raise failure

    pdf_path = tmp_path / "malformed.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setattr("newsdom_api.main.PdfReader", reject_pdf)

    with pytest.raises(HTTPException) as exc_info:
        _validate_pdf_structure(pdf_path)

    assert exc_info.value.status_code == 415
    assert exc_info.value.detail == "Unsupported Media Type"
    assert exc_info.value.__cause__ is None


def test_memory_error_is_operator_visible_without_client_detail(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The legacy MemoryError compatibility case is logged but sanitized."""

    def reject_pdf(_stream: Path, *, strict: bool) -> None:
        assert strict is True
        raise MemoryError("private parser pressure detail")

    pdf_path = tmp_path / "memory-pressure.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setattr("newsdom_api.main.PdfReader", reject_pdf)
    caplog.set_level("ERROR", logger="newsdom_api")

    with pytest.raises(HTTPException) as exc_info:
        _validate_pdf_structure(pdf_path)

    assert exc_info.value.status_code == 415
    assert exc_info.value.detail == "Unsupported Media Type"
    assert "Failed to parse PDF structure" in caplog.text


def test_unexpected_runtime_fault_is_not_misclassified_as_415(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Unexpected integration/server faults must keep the 500-class path."""

    def crash_reader(_stream: Path, *, strict: bool) -> None:
        assert strict is True
        raise RuntimeError("unexpected parser integration fault")

    pdf_path = tmp_path / "runtime-fault.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setattr("newsdom_api.main.PdfReader", crash_reader)

    with pytest.raises(RuntimeError, match="unexpected parser integration fault"):
        _validate_pdf_structure(pdf_path)

"""Regression tests for the PDF validation exception boundary."""

from __future__ import annotations

from fastapi import HTTPException
import pytest

import newsdom_api.main as main_module



def _pdf_fixture(tmp_path):
    """Create the smallest header-bearing file needed to enter PdfReader validation."""

    pdf_path = tmp_path / "candidate.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
    return pdf_path


def test_pdf_validation_maps_known_parser_resource_failure_to_415(
    monkeypatch,
    tmp_path,
) -> None:
    """Known parser exhaustion remains a bounded invalid-media response."""

    def reject_pdf(_stream, *, strict):
        assert strict is True
        raise MemoryError("simulated parser exhaustion")

    monkeypatch.setattr(main_module, "PdfReader", reject_pdf)

    with pytest.raises(HTTPException) as exc_info:
        main_module._validate_pdf_structure(_pdf_fixture(tmp_path))

    assert exc_info.value.status_code == 415
    assert exc_info.value.detail == main_module.UNSUPPORTED_MEDIA_DETAIL


def test_pdf_validation_does_not_mask_unexpected_runtime_defects(
    monkeypatch,
    tmp_path,
) -> None:
    """Unexpected implementation faults must reach the sanitized 500 boundary."""

    def fail_unexpectedly(_stream, *, strict):
        assert strict is True
        raise RuntimeError("unexpected validator defect")

    monkeypatch.setattr(main_module, "PdfReader", fail_unexpectedly)

    with pytest.raises(RuntimeError, match="unexpected validator defect"):
        main_module._validate_pdf_structure(_pdf_fixture(tmp_path))

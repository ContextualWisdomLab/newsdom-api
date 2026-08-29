from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from newsdom_api.config import AuthenticationMode, RuntimeProfile, RuntimeSettings
from newsdom_api.main import _validate_pdf_structure, create_app


def _write_pdf(path: Path) -> Path:
    """Write the smallest magic-bearing fixture needed to reach PdfReader."""

    path.write_bytes(b"%PDF-1.4\n%%EOF")
    return path


def _development_app():
    """Create an explicitly auth-disabled development app for parser-boundary tests."""

    return create_app(
        RuntimeSettings(
            authentication_mode=AuthenticationMode.DISABLED,
            runtime_profile=RuntimeProfile.DEVELOPMENT,
        ),
        runtime_readiness_probe=lambda: True,
    )


from fastapi import HTTPException


def test_pdf_validation_propagates_unexpected_parser_fault(monkeypatch, tmp_path):
    """Unexpected parser/runtime failures must not masquerade as invalid input."""

    def fail_reader(_stream, *, strict):
        assert strict is True
        raise MemoryError("synthetic parser resource failure")

    monkeypatch.setattr("newsdom_api.main.PdfReader", fail_reader)

    with pytest.raises(HTTPException) as exc_info:
        _validate_pdf_structure(_write_pdf(tmp_path / "fixture.pdf"))

    assert exc_info.value.status_code == 415
    assert exc_info.value.detail == "Unsupported Media Type"


def test_parse_endpoint_sanitizes_unexpected_parser_fault_as_500(monkeypatch):
    """The application error boundary must sanitize unexpected PDF failures."""

    def fail_reader(_stream, *, strict):
        assert strict is True
        raise RuntimeError("synthetic parser defect")

    monkeypatch.setattr("newsdom_api.main.PdfReader", fail_reader)

    client = TestClient(_development_app(), raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"

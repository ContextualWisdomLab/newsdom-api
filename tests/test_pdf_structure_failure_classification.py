from pathlib import Path

import pytest

from newsdom_api.main import _validate_pdf_structure


def test_validate_pdf_structure_does_not_mask_internal_runtime_faults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unexpected server faults must remain 500-class instead of client 415 errors."""

    def crash_reader(_stream: Path, *, strict: bool) -> None:
        assert strict is True
        raise RuntimeError("unexpected parser integration fault")

    pdf_path = tmp_path / "runtime-fault.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setattr("newsdom_api.main.PdfReader", crash_reader)

    with pytest.raises(RuntimeError, match="unexpected parser integration fault"):
        _validate_pdf_structure(pdf_path)

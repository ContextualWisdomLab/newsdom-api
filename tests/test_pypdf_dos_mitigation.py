import pytest
from unittest.mock import patch
from pathlib import Path
from fastapi import HTTPException
from newsdom_api.main import _validate_pdf_structure, UNSUPPORTED_MEDIA_DETAIL


def test_validate_pdf_structure_broad_exception_handling(tmp_path: Path):
    pdf_path = tmp_path / "fake.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 mock content")

    with patch("newsdom_api.main.PdfReader") as mock_reader:
        mock_reader.side_effect = MemoryError("Simulated memory exhaustion")

        with pytest.raises(HTTPException) as exc_info:
            _validate_pdf_structure(pdf_path)

        assert exc_info.value.status_code == 415
        assert exc_info.value.detail == UNSUPPORTED_MEDIA_DETAIL

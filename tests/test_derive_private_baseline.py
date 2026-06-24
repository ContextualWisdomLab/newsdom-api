from __future__ import annotations

import json
from pathlib import Path

from unittest.mock import MagicMock, patch
import sys

import pytest
from fastapi import HTTPException
from tools.derive_private_baseline import derive_baseline
from tools import derive_private_baseline


@patch("tools.derive_private_baseline.parse_pdf_bytes")
def test_derive_private_baseline_direct_call(
    mock_parse_pdf_bytes, tmp_path: Path
) -> None:
    """The script's core logic should run on a directory of PDFs and output a JSON baseline."""
    # Arrange
    # Create a dummy PDF file for the test
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    dummy_pdf_path = fixtures_dir / "dummy.pdf"
    # A minimal valid PDF file content (one empty page)
    dummy_pdf_content = b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000058 00000 n\n0000000111 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF"
    dummy_pdf_path.write_bytes(dummy_pdf_content)

    output_json_path = tmp_path / "baseline.json"

    # Mock the parse_pdf_bytes response
    mock_response = MagicMock()

    # Create two pages, one with a headline, one without, to test iteration logic
    mock_page1 = MagicMock()
    mock_page1.page_number = 1
    mock_article1 = MagicMock()
    mock_article1.headline = "Headline 1"
    mock_article2 = MagicMock()
    mock_article2.headline = None
    mock_page1.articles = [mock_article1, mock_article2]

    mock_page2 = MagicMock()
    mock_page2.page_number = 2
    mock_page2.articles = []

    mock_response.pages = [mock_page1, mock_page2]
    mock_parse_pdf_bytes.return_value = mock_response

    # Act
    derive_baseline(fixtures_dir, output_json_path)

    # Assert
    assert output_json_path.exists()
    baseline_data = json.loads(output_json_path.read_text())

    # Check for the structure and expected redacted metrics
    assert "notes" in baseline_data
    assert "page_count" in baseline_data
    assert "headline_page_coverage" in baseline_data
    assert "article_count" in baseline_data

    # We mocked 2 pages and 2 articles, with headlines on page 1.
    assert baseline_data["page_count"] == 2
    assert baseline_data["article_count"] == 2
    assert baseline_data["headline_page_coverage"] == 0.5


def test_derive_baseline_no_pdfs(tmp_path: Path) -> None:
    """If the directory contains no PDFs, a FileNotFoundError should be raised."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    output_path = tmp_path / "baseline.json"

    with pytest.raises(FileNotFoundError, match="No PDF files found in"):
        derive_baseline(empty_dir, output_path)


@patch("tools.derive_private_baseline.parse_pdf_bytes")
def test_derive_baseline_http_exception(mock_parse_pdf_bytes, tmp_path: Path) -> None:
    """If parse_pdf_bytes raises HTTPException, it should be wrapped in RuntimeError."""
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    dummy_pdf_path = fixtures_dir / "dummy.pdf"
    dummy_pdf_path.write_bytes(b"dummy pdf content")
    output_path = tmp_path / "baseline.json"

    mock_parse_pdf_bytes.side_effect = HTTPException(
        status_code=503, detail="MinerU timeout"
    )

    with pytest.raises(
        RuntimeError, match="OCR processing failed for dummy.pdf: MinerU timeout"
    ):
        derive_baseline(fixtures_dir, output_path)


@patch("tools.derive_private_baseline.derive_baseline")
def test_main_success(mock_derive_baseline, tmp_path: Path) -> None:
    """main() should complete normally when no exceptions are raised."""
    fixtures_dir = tmp_path / "fixtures"
    output_path = tmp_path / "baseline.json"

    test_args = [
        "derive_private_baseline.py",
        "--private-fixtures-dir",
        str(fixtures_dir),
        str(output_path),
    ]
    with patch.object(sys, "argv", test_args):
        derive_private_baseline.main()

    mock_derive_baseline.assert_called_once_with(fixtures_dir, output_path)


@patch("tools.derive_private_baseline.derive_baseline")
def test_main_runtime_error(mock_derive_baseline, tmp_path: Path, capsys) -> None:
    """main() should exit(1) and print error if a known error occurs."""
    fixtures_dir = tmp_path / "fixtures"
    output_path = tmp_path / "baseline.json"

    mock_derive_baseline.side_effect = RuntimeError("Mocked runtime error")

    test_args = [
        "derive_private_baseline.py",
        "--private-fixtures-dir",
        str(fixtures_dir),
        str(output_path),
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            derive_private_baseline.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert (
        "Error: Failed to derive baseline. Reason: Mocked runtime error" in captured.err
    )


@patch("tools.derive_private_baseline.derive_baseline")
def test_main_unexpected_error(mock_derive_baseline, tmp_path: Path, capsys) -> None:
    """main() should exit(1) and print error if an unexpected error occurs."""
    fixtures_dir = tmp_path / "fixtures"
    output_path = tmp_path / "baseline.json"

    mock_derive_baseline.side_effect = Exception("Unexpected failure")

    test_args = [
        "derive_private_baseline.py",
        "--private-fixtures-dir",
        str(fixtures_dir),
        str(output_path),
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            derive_private_baseline.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "An unexpected error occurred: Unexpected failure" in captured.err

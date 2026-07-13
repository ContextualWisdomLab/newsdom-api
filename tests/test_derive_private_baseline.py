from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.derive_private_baseline import derive_baseline


@pytest.mark.xfail(
    reason="The dummy PDF is too simple and causes mineru to exit with an error. A more realistic PDF is needed for this integration test."
)
def test_derive_private_baseline_direct_call(tmp_path: Path) -> None:
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

    # For our dummy single-page PDF, we expect simple values
    # The dummy PDF has no parsable content, so the service returns a default DOM.
    assert baseline_data["page_count"] == 1
    assert baseline_data["article_count"] == 0
    assert baseline_data["headline_page_coverage"] == 0.0

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


def test_derive_baseline_recursive_and_strict(tmp_path: Path):
    from unittest.mock import patch
    from fastapi import HTTPException
    from newsdom_api.schemas import ArticleNode, PageNode, ParseResponse

    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    (fixtures_dir / "dummy1.pdf").write_bytes(b"content 1")

    sub_dir = fixtures_dir / "sub"
    sub_dir.mkdir()
    (sub_dir / "dummy2.pdf").write_bytes(b"content 2")

    output_path = tmp_path / "baseline.json"

    mock_article = ArticleNode(article_id="1", headline="test headline")
    mock_article2 = ArticleNode(article_id="2", headline="")
    mock_page = PageNode(page_number=1, articles=[mock_article, mock_article2])
    mock_response = ParseResponse(document_id="test", pages=[mock_page])

    with patch("tools.derive_private_baseline.parse_pdf_bytes") as mock_parse:
        # First file succeeds, second file fails
        mock_parse.side_effect = [
            mock_response,
            HTTPException(status_code=500, detail="MinerU failed"),
        ]

        # Test non-strict mode: Should catch exception and continue
        derive_baseline(fixtures_dir, output_path, recursive=True, strict=False)
        assert output_path.exists()

        data = json.loads(output_path.read_text())
        assert data["page_count"] == 1
        assert data["article_count"] == 2
        assert data["headline_page_coverage"] == 1.0


def test_derive_baseline_no_headline_coverage(tmp_path: Path):
    from unittest.mock import patch
    from newsdom_api.schemas import PageNode, ParseResponse

    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    (fixtures_dir / "dummy.pdf").write_bytes(b"content")
    output_path = tmp_path / "baseline.json"

    # A response with no articles means total_pages > 0, but no headlines
    mock_page = PageNode(page_number=1, articles=[])
    mock_response = ParseResponse(document_id="test", pages=[mock_page])

    with patch(
        "tools.derive_private_baseline.parse_pdf_bytes", return_value=mock_response
    ):
        derive_baseline(fixtures_dir, output_path)

        data = json.loads(output_path.read_text())
        assert data["page_count"] == 1
        assert data["article_count"] == 0
        assert data["headline_page_coverage"] == 0.0


def test_derive_baseline_if_name_main_runpy(tmp_path: Path):
    import runpy
    import sys
    from unittest.mock import patch

    with patch.object(sys, "argv", ["derive_private_baseline.py", "--help"]):
        try:
            runpy.run_module("tools.derive_private_baseline", run_name="__main__")
        except SystemExit as e:
            assert e.code == 0


def test_derive_baseline_strict_raises(tmp_path: Path):
    from unittest.mock import patch
    from fastapi import HTTPException

    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    (fixtures_dir / "dummy1.pdf").write_bytes(b"content 1")
    output_path = tmp_path / "baseline.json"

    with patch("tools.derive_private_baseline.parse_pdf_bytes") as mock_parse:
        mock_parse.side_effect = HTTPException(status_code=500, detail="MinerU failed")

        with pytest.raises(RuntimeError, match="OCR processing failed"):
            derive_baseline(fixtures_dir, output_path, strict=True)


def test_derive_baseline_no_pdfs(tmp_path: Path):
    fixtures_dir = tmp_path / "empty"
    fixtures_dir.mkdir()
    output_path = tmp_path / "baseline.json"

    with pytest.raises(FileNotFoundError, match="No PDF files found"):
        derive_baseline(fixtures_dir, output_path)


def test_derive_baseline_main_success(tmp_path: Path):
    from tools.derive_private_baseline import main
    from unittest.mock import patch

    fixtures_dir = tmp_path / "fixtures"
    output_path = tmp_path / "baseline.json"

    with patch("tools.derive_private_baseline.derive_baseline") as mock_derive:
        main(
            [
                "--private-fixtures-dir",
                str(fixtures_dir),
                str(output_path),
                "--recursive",
                "--no-strict",
            ]
        )
        mock_derive.assert_called_once_with(fixtures_dir, output_path, True, False)


def test_derive_baseline_main_known_error(tmp_path: Path):
    from tools.derive_private_baseline import main
    from unittest.mock import patch

    fixtures_dir = tmp_path / "fixtures"
    output_path = tmp_path / "baseline.json"

    with patch(
        "tools.derive_private_baseline.derive_baseline",
        side_effect=RuntimeError("Some error"),
    ):
        with pytest.raises(SystemExit) as e:
            main(["--private-fixtures-dir", str(fixtures_dir), str(output_path)])
        assert e.value.code == 1


def test_derive_baseline_main_unknown_error(tmp_path: Path):
    from tools.derive_private_baseline import main
    from unittest.mock import patch
    import builtins

    fixtures_dir = tmp_path / "fixtures"
    output_path = tmp_path / "baseline.json"

    class CustomError(Exception):
        pass

    with patch(
        "tools.derive_private_baseline.derive_baseline",
        side_effect=CustomError("Unknown error"),
    ):
        with pytest.raises(SystemExit) as e:
            main(["--private-fixtures-dir", str(fixtures_dir), str(output_path)])
        assert e.value.code == 1


def test_derive_baseline_if_name_main():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "tools.derive_private_baseline", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--private-fixtures-dir" in result.stdout

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from newsdom_api.errors import MineruRuntimeUnavailableError
from newsdom_api.schemas import ArticleNode, PageNode, ParseResponse
from tools import derive_private_baseline
from tools.derive_private_baseline import derive_baseline


@patch("tools.derive_private_baseline.parse_pdf_bytes")
def test_derive_private_baseline_direct_call(
    mock_parse_pdf_bytes, tmp_path: Path
) -> None:
    """The core logic should derive redacted metrics from parsed PDF pages."""
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    dummy_pdf_path = fixtures_dir / "dummy.pdf"
    dummy_pdf_path.write_bytes(b"%PDF-1.0\n%%EOF")
    output_json_path = tmp_path / "baseline.json"

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

    mock_response = MagicMock()
    mock_response.pages = [mock_page1, mock_page2]
    mock_parse_pdf_bytes.return_value = mock_response

    derive_baseline(fixtures_dir, output_json_path)

    baseline_data = json.loads(output_json_path.read_text())
    assert baseline_data["page_count"] == 2
    assert baseline_data["article_count"] == 2
    assert baseline_data["headline_page_coverage"] == 0.5
    assert "notes" in baseline_data


def test_derive_baseline_recursive_and_non_strict(tmp_path: Path, capsys) -> None:
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
        mock_parse.side_effect = [
            mock_response,
            MineruRuntimeUnavailableError(),
        ]

        derive_baseline(fixtures_dir, output_path, recursive=True, strict=False)

    data = json.loads(output_path.read_text())
    assert data["page_count"] == 1
    assert data["article_count"] == 2
    assert data["headline_page_coverage"] == 1.0
    assert "OCR processing failed for dummy2.pdf" in capsys.readouterr().err


def test_derive_baseline_no_headline_coverage(tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    (fixtures_dir / "dummy.pdf").write_bytes(b"content")
    output_path = tmp_path / "baseline.json"

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


def test_derive_baseline_strict_raises(tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    (fixtures_dir / "dummy1.pdf").write_bytes(b"content 1")
    output_path = tmp_path / "baseline.json"

    with patch("tools.derive_private_baseline.parse_pdf_bytes") as mock_parse:
        mock_parse.side_effect = MineruRuntimeUnavailableError()

        with pytest.raises(RuntimeError, match="OCR processing failed"):
            derive_baseline(fixtures_dir, output_path, strict=True)


def test_derive_baseline_no_pdfs(tmp_path: Path) -> None:
    """If the directory contains no PDFs, FileNotFoundError is raised."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="No PDF files found in"):
        derive_baseline(empty_dir, tmp_path / "baseline.json")


@patch("tools.derive_private_baseline.parse_pdf_bytes")
def test_derive_baseline_http_exception(
    mock_parse_pdf_bytes, tmp_path: Path
) -> None:
    """HTTPException from parse_pdf_bytes should be wrapped in RuntimeError."""
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    (fixtures_dir / "dummy.pdf").write_bytes(b"dummy pdf content")
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

    derive_private_baseline.main(
        ["--private-fixtures-dir", str(fixtures_dir), str(output_path)]
    )

    mock_derive_baseline.assert_called_once_with(
        fixtures_dir, output_path, False, True
    )


@patch("tools.derive_private_baseline.derive_baseline")
def test_main_success_with_options(mock_derive_baseline, tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    output_path = tmp_path / "baseline.json"

    derive_private_baseline.main(
        [
            "--private-fixtures-dir",
            str(fixtures_dir),
            str(output_path),
            "--recursive",
            "--no-strict",
        ]
    )

    mock_derive_baseline.assert_called_once_with(
        fixtures_dir, output_path, True, False
    )


@patch("tools.derive_private_baseline.derive_baseline")
def test_main_runtime_error(mock_derive_baseline, tmp_path: Path, capsys) -> None:
    """main() should exit(1) and print a known error."""
    fixtures_dir = tmp_path / "fixtures"
    output_path = tmp_path / "baseline.json"

    mock_derive_baseline.side_effect = RuntimeError("Mocked runtime error")

    with pytest.raises(SystemExit) as exc_info:
        derive_private_baseline.main(
            ["--private-fixtures-dir", str(fixtures_dir), str(output_path)]
        )

    assert exc_info.value.code == 1
    assert (
        "Error: Failed to derive baseline. Reason: Mocked runtime error"
        in capsys.readouterr().err
    )


@patch("tools.derive_private_baseline.derive_baseline")
def test_main_unexpected_error(
    mock_derive_baseline, tmp_path: Path, capsys
) -> None:
    """main() should exit(1) and print an unexpected error."""
    fixtures_dir = tmp_path / "fixtures"
    output_path = tmp_path / "baseline.json"

    mock_derive_baseline.side_effect = Exception("Unexpected failure")

    with pytest.raises(SystemExit) as exc_info:
        derive_private_baseline.main(
            ["--private-fixtures-dir", str(fixtures_dir), str(output_path)]
        )

    assert exc_info.value.code == 1
    assert "An unexpected error occurred: Unexpected failure" in capsys.readouterr().err


def test_derive_baseline_module_help() -> None:
    env = {
        **os.environ,
        "PYTHONPATH": str(Path.cwd() / "src"),
    }
    result = subprocess.run(
        [sys.executable, "-m", "tools.derive_private_baseline", "--help"],
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.returncode == 0
    assert "--private-fixtures-dir" in result.stdout

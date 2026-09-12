from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tools import benchmark_ocr


@pytest.fixture
def mock_pdf_dir(tmp_path: Path) -> Path:
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    (pdf_dir / "doc1.pdf").write_text("dummy pdf 1")
    (pdf_dir / "doc2.pdf").write_text("dummy pdf 2")
    (pdf_dir / "doc3.pdf").write_text("dummy pdf 3")

    sub_dir = pdf_dir / "sub"
    sub_dir.mkdir()
    (sub_dir / "doc4.pdf").write_text("dummy pdf 4")
    return pdf_dir


def test_benchmark_ocr_harness_json(mock_pdf_dir: Path, tmp_path: Path) -> None:
    """The harness should aggregate success, failure, and timeout results."""
    output_path = tmp_path / "results.json"

    mock_engine1 = MagicMock(return_value={"status": "success", "page_count": 2})
    mock_engine2 = MagicMock()
    mock_engine2.side_effect = [
        subprocess.TimeoutExpired(cmd="engine2", timeout=10),
        RuntimeError("OCR process failed"),
        {"status": "success", "page_count": 1},
    ]

    engines = {
        "engine1": mock_engine1,
        "engine2": mock_engine2,
    }

    with patch.dict(benchmark_ocr.OCR_ENGINES, engines):
        benchmark_ocr.main(
            [
                "--fixtures-dir",
                str(mock_pdf_dir),
                "--output",
                str(output_path),
                "--engines",
                "engine1",
                "engine2",
            ]
        )

    results = json.loads(output_path.read_text())

    assert results["engine1"]["success"] == 3
    assert results["engine1"]["failed"] == 0
    assert results["engine1"]["timed_out"] == 0
    assert "doc1.pdf" in results["engine1"]["results"]
    assert results["engine1"]["results"]["doc1.pdf"]["status"] == "success"

    assert results["engine2"]["success"] == 1
    assert results["engine2"]["failed"] == 1
    assert results["engine2"]["timed_out"] == 1
    assert results["engine2"]["results"]["doc1.pdf"]["status"] == "timed_out"
    assert results["engine2"]["results"]["doc2.pdf"]["status"] == "failed"
    assert "OCR process failed" in results["engine2"]["results"]["doc2.pdf"]["error"]
    assert results["engine2"]["results"]["doc3.pdf"]["status"] == "success"

    assert results["summary"]["total_files"] == 3
    assert results["summary"]["total_runs"] == 6


def test_benchmark_ocr_recursive_and_csv(mock_pdf_dir: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "results.csv"

    mock_engine = MagicMock(return_value={"status": "success", "page_count": 2})

    with patch.dict(benchmark_ocr.OCR_ENGINES, {"engine1": mock_engine}):
        benchmark_ocr.main(
            [
                "--fixtures-dir",
                str(mock_pdf_dir),
                "--output",
                str(output_path),
                "--engines",
                "engine1",
                "--recursive",
                "--format",
                "csv",
            ]
        )

    csv_text = output_path.read_text()
    assert "doc1.pdf" in csv_text
    assert "doc2.pdf" in csv_text
    assert "doc3.pdf" in csv_text
    assert "doc4.pdf" in csv_text


def test_benchmark_ocr_no_pdfs(tmp_path: Path) -> None:
    """If the fixtures directory contains no PDFs, FileNotFoundError is raised."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="No PDF files found in"):
        benchmark_ocr.main(
            [
                "--fixtures-dir",
                str(empty_dir),
                "--output",
                str(tmp_path / "results.json"),
            ]
        )


def test_benchmark_ocr_unknown_engine(mock_pdf_dir: Path, tmp_path: Path) -> None:
    """If an unknown engine is specified, ValueError is raised."""
    with pytest.raises(ValueError, match="Unknown engine: fake_engine"):
        benchmark_ocr.main(
            [
                "--fixtures-dir",
                str(mock_pdf_dir),
                "--output",
                str(tmp_path / "results.json"),
                "--engines",
                "fake_engine",
            ]
        )


@patch("tools.benchmark_ocr.parse_pdf_bytes")
def test_run_mineru_engine(mock_parse_pdf_bytes, tmp_path: Path) -> None:
    """run_mineru_engine should call parse_pdf_bytes and return metrics."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"dummy pdf content")

    mock_response = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.articles = ["article1", "article2"]
    mock_page2 = MagicMock()
    mock_page2.articles = ["article3"]
    mock_response.pages = [mock_page1, mock_page2]
    mock_parse_pdf_bytes.return_value = mock_response

    result = benchmark_ocr.run_mineru_engine(pdf_path)

    mock_parse_pdf_bytes.assert_called_once_with(
        b"dummy pdf content", filename="sample.pdf"
    )
    assert result == {
        "status": "success",
        "page_count": 2,
        "article_count": 3,
    }

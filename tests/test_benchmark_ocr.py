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


def test_benchmark_ocr_harness_json(mock_pdf_dir: Path, tmp_path: Path):
    """
    The benchmark harness should run a set of engines against a corpus of PDFs
    and correctly aggregate success, failure, and timeout results.
    """
    output_path = tmp_path / "results.json"

    # Mock engine runners
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

    assert output_path.exists()
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


def test_benchmark_ocr_recursive_and_csv(mock_pdf_dir: Path, tmp_path: Path):
    output_path = tmp_path / "results.csv"

    mock_engine1 = MagicMock(return_value={"status": "success", "page_count": 2})
    engines = {"engine1": mock_engine1}

    with patch.dict(benchmark_ocr.OCR_ENGINES, engines):
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

    assert output_path.exists()

    csv_text = output_path.read_text()
    assert "doc1.pdf" in csv_text
    assert "doc2.pdf" in csv_text
    assert "doc3.pdf" in csv_text
    assert "doc4.pdf" in csv_text


def test_benchmark_ocr_unknown_engine(mock_pdf_dir: Path, tmp_path: Path):
    output_path = tmp_path / "results.json"
    with pytest.raises(ValueError, match="Unknown engine: unknown_engine"):
        benchmark_ocr.main(
            [
                "--fixtures-dir",
                str(mock_pdf_dir),
                "--output",
                str(output_path),
                "--engines",
                "unknown_engine",
            ]
        )


def test_benchmark_ocr_no_pdfs(tmp_path: Path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    output_path = tmp_path / "results.json"
    with pytest.raises(FileNotFoundError, match="No PDF files found"):
        benchmark_ocr.main(
            [
                "--fixtures-dir",
                str(empty_dir),
                "--output",
                str(output_path),
            ]
        )


@patch("tools.benchmark_ocr.parse_pdf_bytes")
def test_run_mineru_engine(mock_parse_pdf_bytes, tmp_path: Path):
    from newsdom_api.schemas import ArticleNode, PageNode, ParseResponse

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"test pdf content")

    mock_article = ArticleNode(article_id="1", headline="test")
    mock_page = PageNode(page_number=1, articles=[mock_article])
    mock_response = ParseResponse(document_id="test", pages=[mock_page])
    mock_parse_pdf_bytes.return_value = mock_response

    result = benchmark_ocr.run_mineru_engine(pdf_path)

    assert result["status"] == "success"
    assert result["page_count"] == 1
    assert result["article_count"] == 1
    mock_parse_pdf_bytes.assert_called_once_with(
        b"test pdf content", filename="test.pdf"
    )


@patch(
    "sys.argv",
    ["benchmark_ocr.py", "--fixtures-dir", "dummy_dir", "--output", "dummy.json"],
)
@patch("tools.benchmark_ocr.run_benchmark")
def test_main_block(mock_run_benchmark):

    # The actual __main__ execution is wrapped in main(), so just import and call it
    # We patch sys.argv to ensure argparse behaves as expected.
    with patch(
        "sys.argv",
        ["benchmark_ocr.py", "--fixtures-dir", "dummy_dir", "--output", "dummy.json"],
    ):
        benchmark_ocr.main()
    mock_run_benchmark.assert_called_once_with(
        Path("dummy_dir"), Path("dummy.json"), ["mineru"], False, "json"
    )


def test_if_name_main(tmp_path: Path):
    import runpy
    import sys
    from unittest.mock import patch

    with patch.object(sys, "argv", ["benchmark_ocr.py", "--help"]):
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            try:
                runpy.run_module("tools.benchmark_ocr", run_name="__main__")
            except SystemExit as e:
                assert e.code == 0

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
    return pdf_dir


def test_benchmark_ocr_harness(mock_pdf_dir: Path, tmp_path: Path):
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

    # Assert engine1 (always succeeds)
    assert results["engine1"]["success"] == 3
    assert results["engine1"]["failed"] == 0
    assert results["engine1"]["timed_out"] == 0
    assert "doc1.pdf" in results["engine1"]["results"]
    assert results["engine1"]["results"]["doc1.pdf"]["status"] == "success"

    # Assert engine2 (fails, times out, then succeeds)
    assert results["engine2"]["success"] == 1
    assert results["engine2"]["failed"] == 1
    assert results["engine2"]["timed_out"] == 1
    assert results["engine2"]["results"]["doc1.pdf"]["status"] == "timed_out"
    assert results["engine2"]["results"]["doc2.pdf"]["status"] == "failed"
    assert "OCR process failed" in results["engine2"]["results"]["doc2.pdf"]["error"]
    assert results["engine2"]["results"]["doc3.pdf"]["status"] == "success"

    # Check summary
    assert results["summary"]["total_files"] == 3
    assert results["summary"]["total_runs"] == 6

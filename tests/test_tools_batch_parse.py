from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tools import batch_parse_pdf


@pytest.fixture
def mock_pdf_dir(tmp_path: Path) -> Path:
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    (pdf_dir / "doc1.pdf").write_bytes(b"content1")
    (pdf_dir / "doc2.pdf").write_bytes(b"content2")
    return pdf_dir


@patch("tools.batch_parse_pdf.parse_pdf_bytes")
def test_batch_parse_success(mock_parse, mock_pdf_dir, tmp_path, capsys):
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {"status": "ok"}
    mock_parse.return_value = mock_response

    out_dir = tmp_path / "out"
    batch_parse_pdf.main([str(mock_pdf_dir), str(out_dir)])

    assert (out_dir / "doc1.json").exists()
    assert (out_dir / "doc2.json").exists()

    out = capsys.readouterr().out
    assert "Batch parse complete: 2 succeeded, 0 failed." in out


@patch("tools.batch_parse_pdf.parse_pdf_bytes")
def test_batch_parse_recursive_preserves_relative_paths(mock_parse, mock_pdf_dir, tmp_path):
    nested_dir = mock_pdf_dir / "section"
    nested_dir.mkdir()
    (nested_dir / "doc3.pdf").write_bytes(b"content3")

    mock_response = MagicMock()
    mock_response.model_dump.return_value = {"status": "ok"}
    mock_parse.return_value = mock_response

    out_dir = tmp_path / "out"
    batch_parse_pdf.main([str(mock_pdf_dir), str(out_dir), "--recursive"])

    assert (out_dir / "doc1.json").exists()
    assert (out_dir / "doc2.json").exists()
    assert (out_dir / "section" / "doc3.json").exists()
    assert mock_parse.call_count == 3


@patch("tools.batch_parse_pdf.parse_pdf_bytes")
def test_batch_parse_partial_failure(mock_parse, mock_pdf_dir, tmp_path, capsys):
    def side_effect(b, filename):
        if filename == "doc2.pdf":
            raise Exception("Fail")
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {"status": "ok"}
        return mock_response

    mock_parse.side_effect = side_effect

    out_dir = tmp_path / "out"
    batch_parse_pdf.main([str(mock_pdf_dir), str(out_dir)])

    assert (out_dir / "doc1.json").exists()
    assert not (out_dir / "doc2.json").exists()

    err = capsys.readouterr().err
    assert "Failed to parse doc2.pdf" in err


def test_batch_parse_not_a_dir(tmp_path, capsys):
    not_dir = tmp_path / "not_dir.txt"
    not_dir.write_text("test")

    with pytest.raises(SystemExit) as e:
        batch_parse_pdf.main([str(not_dir), str(tmp_path / "out")])

    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "Input is not a directory" in err


def test_batch_parse_no_pdfs(tmp_path, capsys):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    batch_parse_pdf.main([str(empty_dir), str(tmp_path / "out")])

    out = capsys.readouterr().out
    assert "No PDF files found" in out

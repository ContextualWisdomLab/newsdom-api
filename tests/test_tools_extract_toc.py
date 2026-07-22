from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.extract_toc import extract_toc, main


@pytest.fixture
def sample_dom_path(tmp_path: Path) -> Path:
    """Fixture providing a sample DOM for TOC extraction."""
    data = {
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"article_id": "a1", "headline": "First Title"},
                    {"article_id": "a2", "headline": "(untitled)"},
                ],
            },
            {
                "page_number": 2,
                "articles": [{"article_id": "a3", "headline": "Second Title"}],
            },
        ]
    }
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_extract_toc_json(sample_dom_path: Path) -> None:
    """Test extracting TOC as JSON."""
    result = extract_toc(sample_dom_path, output_format="json")
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == {
        "page_number": 1,
        "article_id": "a1",
        "headline": "First Title",
    }
    assert result[1] == {
        "page_number": 2,
        "article_id": "a3",
        "headline": "Second Title",
    }


def test_extract_toc_text(sample_dom_path: Path) -> None:
    """Test extracting TOC as plain text."""
    result = extract_toc(sample_dom_path, output_format="text")
    assert isinstance(result, str)
    assert "Table of Contents" in result
    assert "Page 1: First Title (a1)" in result
    assert "Page 2: Second Title (a3)" in result
    assert "(untitled)" not in result


def test_extract_toc_invalid_file(tmp_path: Path) -> None:
    """Test error handling for non-existent file."""
    path = tmp_path / "not_found.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        extract_toc(path)


def test_extract_toc_invalid_extension(tmp_path: Path) -> None:
    """Test error handling for non-json extension."""
    path = tmp_path / "data.txt"
    path.write_text("{}")
    with pytest.raises(ValueError, match="must be a .json file"):
        extract_toc(path)


def test_extract_toc_invalid_json(tmp_path: Path) -> None:
    """Test error handling for malformed JSON."""
    path = tmp_path / "bad.json"
    path.write_text("{bad json")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        extract_toc(path)


def test_main_text_stdout(sample_dom_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test main entry point outputting text to stdout."""
    main([str(sample_dom_path), "--format", "text"])
    captured = capsys.readouterr()
    assert "Table of Contents" in captured.out
    assert "First Title" in captured.out


def test_main_json_stdout(sample_dom_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test main entry point outputting JSON to stdout."""
    main([str(sample_dom_path), "--format", "json"])
    captured = capsys.readouterr()
    assert '"headline": "First Title"' in captured.out


def test_main_text_file(
    sample_dom_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test main entry point outputting text to a file."""
    out_path = tmp_path / "out.txt"
    main([str(sample_dom_path), "--format", "text", "--output", str(out_path)])

    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Table of Contents" in content

    captured = capsys.readouterr()
    assert "TOC saved to" in captured.out


def test_main_json_file(
    sample_dom_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test main entry point outputting JSON to a file."""
    out_path = tmp_path / "out.json"
    main([str(sample_dom_path), "--format", "json", "--output", str(out_path)])

    assert out_path.exists()
    content = json.loads(out_path.read_text(encoding="utf-8"))
    assert isinstance(content, list)
    assert len(content) == 2

    captured = capsys.readouterr()
    assert "TOC saved to" in captured.out


def test_main_error_handling(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test main entry point error catch."""
    not_found = tmp_path / "nope.json"
    with pytest.raises(SystemExit) as exc:
        main([str(not_found)])
    assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "Error: File not found" in captured.err

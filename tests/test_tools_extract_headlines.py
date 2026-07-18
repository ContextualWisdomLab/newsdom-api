import json
import pytest
from pathlib import Path
from tools.extract_headlines import extract_headlines, main


def test_extract_headlines_valid(tmp_path: Path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.txt"
    data = {
        "document_id": "test",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"article_id": "a1", "headline": "Headline 1", "body_blocks": []},
                    {"article_id": "a2", "headline": "Headline 2", "body_blocks": []},
                ],
            }
        ],
        "quality": {"status": "success", "parser": "test", "warnings": []},
    }
    input_path.write_text(json.dumps(data), encoding="utf-8")
    extract_headlines(input_path, output_path)
    result = output_path.read_text(encoding="utf-8")
    assert result == "Headline 1\nHeadline 2\n"


def test_extract_headlines_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        extract_headlines(tmp_path / "nonexistent.json", tmp_path / "output.txt")


def test_extract_headlines_invalid_extension(tmp_path: Path):
    invalid_file = tmp_path / "input.txt"
    invalid_file.touch()
    with pytest.raises(ValueError, match="must be a .json file"):
        extract_headlines(invalid_file, tmp_path / "output.txt")


def test_extract_headlines_invalid_json(tmp_path: Path):
    input_path = tmp_path / "input.json"
    input_path.write_text("invalid json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        extract_headlines(input_path, tmp_path / "output.txt")


def test_extract_headlines_invalid_schema(tmp_path: Path):
    input_path = tmp_path / "input.json"
    input_path.write_text('{"invalid": "schema"}', encoding="utf-8")
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        extract_headlines(input_path, tmp_path / "output.txt")


def test_main_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.txt"
    data = {
        "document_id": "test",
        "pages": [],
        "quality": {"status": "success", "parser": "test", "warnings": []},
    }
    input_path.write_text(json.dumps(data), encoding="utf-8")
    main([str(input_path), "-o", str(output_path)])
    assert f"Headlines successfully written to {output_path}" in capsys.readouterr().out


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit):
        main([str(tmp_path / "nonexistent.json"), "-o", str(tmp_path / "output.txt")])
    assert "Error extracting headlines" in capsys.readouterr().err


import sys
import importlib
import runpy


def test_extract_headlines_import_path(monkeypatch):
    """Test sys.path injection for coverage."""
    import tools.extract_headlines

    target_path = str(
        Path(tools.extract_headlines.__file__).resolve().parents[1] / "src"
    )
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != target_path])
    importlib.reload(tools.extract_headlines)
    assert target_path in sys.path


def test_extract_headlines_main_module():
    """Test if __name__ == '__main__' block coverage via run_module."""
    try:
        runpy.run_module("tools.extract_headlines", run_name="__main__")
    except SystemExit:
        pass


def test_extract_headlines_empty_headline(tmp_path: Path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.txt"
    data = {
        "document_id": "test",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"article_id": "a1", "headline": "", "body_blocks": []},
                    {"article_id": "a2", "headline": "Headline 2", "body_blocks": []},
                ],
            }
        ],
        "quality": {"status": "success", "parser": "test", "warnings": []},
    }
    input_path.write_text(json.dumps(data), encoding="utf-8")
    extract_headlines(input_path, output_path)
    result = output_path.read_text(encoding="utf-8")
    assert result == "Headline 2\n"

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.export_jsonl import export_jsonl, main


def test_export_jsonl_success(tmp_path: Path):
    input_file = tmp_path / "test.json"
    output_file = tmp_path / "test.jsonl"

    input_data = """
    {
        "document_id": "doc1",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art1",
                        "headline": "Title 1",
                        "body_blocks": ["Block 1", "Block 2"]
                    },
                    "invalid_article"
                ]
            },
            "invalid_page"
        ]
    }
    """
    input_file.write_text(input_data, encoding="utf-8")

    export_jsonl(input_file, output_file)

    assert output_file.exists()
    lines = output_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1

    record = json.loads(lines[0])
    assert record["document_id"] == "doc1"
    assert record["page_number"] == 1
    assert record["article_id"] == "art1"
    assert record["headline"] == "Title 1"
    assert record["body_text"] == "Block 1\nBlock 2"


def test_export_jsonl_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="File not found"):
        export_jsonl(tmp_path / "missing.json", tmp_path / "out.jsonl")


def test_export_jsonl_invalid_extension(tmp_path: Path):
    input_file = tmp_path / "test.txt"
    input_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Input file must be a .json file."):
        export_jsonl(input_file, tmp_path / "out.jsonl")


def test_export_jsonl_invalid_json(tmp_path: Path):
    input_file = tmp_path / "test.json"
    input_file.write_text("{invalid}", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(input_file, tmp_path / "out.jsonl")


@patch("sys.argv", ["export_jsonl.py", "in.json", "out.jsonl"])
def test_main_success(tmp_path: Path, monkeypatch, capsys):
    input_file = tmp_path / "in.json"
    input_file.write_text('{"document_id": "doc"}', encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    try:
        main()
    except SystemExit:
        pass

    captured = capsys.readouterr()
    assert "JSONL successfully written to out.jsonl" in captured.out


@patch("sys.argv", ["export_jsonl.py", "missing.json", "out.jsonl"])
def test_main_failure(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL:" in captured.err

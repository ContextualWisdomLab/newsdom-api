import json
from pathlib import Path
from unittest.mock import patch
import pytest

from tools.export_jsonl import export_jsonl, main


def test_export_jsonl_success(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"

    data = {
        "document_id": "doc123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art1",
                        "headline": "Head",
                        "body_blocks": ["Block 1", "Block 2"]
                    },
                    "invalid_article_type"
                ]
            },
            "invalid_page_type"
        ]
    }
    input_file.write_text(json.dumps(data), encoding="utf-8")

    export_jsonl(input_file, output_file)

    assert output_file.exists()
    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    record = json.loads(lines[0])
    assert record["document_id"] == "doc123"
    assert record["page_number"] == 1
    assert record["article_id"] == "art1"
    assert record["headline"] == "Head"
    assert record["body"] == "Block 1\nBlock 2"


def test_export_jsonl_file_not_found(tmp_path: Path) -> None:
    input_file = tmp_path / "not_found.json"
    output_file = tmp_path / "output.jsonl"
    with pytest.raises(FileNotFoundError, match="File not found"):
        export_jsonl(input_file, output_file)


def test_export_jsonl_wrong_extension(tmp_path: Path) -> None:
    input_file = tmp_path / "input.txt"
    input_file.write_text("{}", encoding="utf-8")
    output_file = tmp_path / "output.jsonl"
    with pytest.raises(ValueError, match="Input file must be a .json file."):
        export_jsonl(input_file, output_file)


def test_export_jsonl_invalid_json(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text("{invalid", encoding="utf-8")
    output_file = tmp_path / "output.jsonl"
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(input_file, output_file)


@patch("sys.argv", ["export_jsonl.py", "input.json", "output.jsonl"])
@patch("tools.export_jsonl.export_jsonl")
def test_main_success(mock_export, capsys) -> None:
    main()
    mock_export.assert_called_once()
    captured = capsys.readouterr()
    assert "JSONL successfully written" in captured.out


@patch("sys.argv", ["export_jsonl.py", "input.txt", "output.jsonl"])
@patch("tools.export_jsonl.export_jsonl")
def test_main_error(mock_export, capsys) -> None:
    mock_export.side_effect = ValueError("Test error")
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL: Test error" in captured.err

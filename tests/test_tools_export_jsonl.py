import json
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.export_jsonl import export_jsonl


@pytest.fixture
def valid_json_path(tmp_path: Path) -> Path:
    data = {
        "document_id": "doc123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art1",
                        "headline": "Headline 1",
                        "body_blocks": ["block 1", "block 2"]
                    },
                    "invalid_article",  # Should be skipped
                    {
                        "article_id": "art2",
                        "headline": "Headline 2",
                        "body_blocks": []
                    }
                ]
            },
            "invalid_page",  # Should be skipped
            {
                "page_number": 2,
                "articles": [
                    {
                        "article_id": "art3",
                        "headline": "Headline 3",
                        "body_blocks": ["block 3"]
                    }
                ]
            }
        ]
    }
    file_path = tmp_path / "valid.json"
    file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return file_path


def test_export_jsonl_success(valid_json_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "output.jsonl"
    export_jsonl(valid_json_path, output_path)

    assert output_path.is_file()
    lines = output_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3

    data1 = json.loads(lines[0])
    assert data1["document_id"] == "doc123"
    assert data1["page_number"] == 1
    assert data1["article_id"] == "art1"
    assert data1["headline"] == "Headline 1"
    assert data1["body_blocks"] == ["block 1", "block 2"]

    data2 = json.loads(lines[1])
    assert data2["document_id"] == "doc123"
    assert data2["page_number"] == 1
    assert data2["article_id"] == "art2"
    assert data2["headline"] == "Headline 2"
    assert data2["body_blocks"] == []

    data3 = json.loads(lines[2])
    assert data3["document_id"] == "doc123"
    assert data3["page_number"] == 2
    assert data3["article_id"] == "art3"
    assert data3["headline"] == "Headline 3"
    assert data3["body_blocks"] == ["block 3"]


def test_export_jsonl_file_not_found(tmp_path: Path) -> None:
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        export_jsonl(tmp_path / "missing.json", output_path)


def test_export_jsonl_invalid_extension(tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    input_path.write_text("{}", encoding="utf-8")
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        export_jsonl(input_path, output_path)


def test_export_jsonl_invalid_json(tmp_path: Path) -> None:
    input_path = tmp_path / "invalid.json"
    input_path.write_text("{invalid json", encoding="utf-8")
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(input_path, output_path)


@patch("sys.argv", ["export_jsonl.py", "input.json", "output.jsonl"])
def test_main_cli_success(valid_json_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output_path = tmp_path / "output.jsonl"
    with patch("sys.argv", ["export_jsonl.py", str(valid_json_path), str(output_path)]):
        import tools.export_jsonl
        tools.export_jsonl.main()

    captured = capsys.readouterr()
    assert f"JSONL successfully written to {output_path}" in captured.out
    assert output_path.is_file()


@patch("sys.argv", ["export_jsonl.py", "missing.json", "output.jsonl"])
def test_main_cli_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing_path = tmp_path / "missing.json"
    output_path = tmp_path / "output.jsonl"
    with patch("sys.argv", ["export_jsonl.py", str(missing_path), str(output_path)]):
        import tools.export_jsonl
        with pytest.raises(SystemExit) as exc_info:
            tools.export_jsonl.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL" in captured.err


def test_run_as_main(valid_json_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output_path = tmp_path / "output.jsonl"
    with patch("sys.argv", ["export_jsonl.py", str(valid_json_path), str(output_path)]):
        sys.modules.pop("tools.export_jsonl", None)
        try:
            runpy.run_module("tools.export_jsonl", run_name="__main__")
        except SystemExit as e:
            assert e.code == 0

    captured = capsys.readouterr()
    assert f"JSONL successfully written to {output_path}" in captured.out
    assert output_path.is_file()

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.export_jsonl import export_jsonl, main

VALID_JSON_DATA = {
    "document_id": "test_doc",
    "pages": [
        {
            "page_number": 1,
            "articles": [
                {
                    "article_id": "art_1",
                    "headline": "Test Headline 1",
                    "body_blocks": ["Block 1", "Block 2"],
                },
                {
                    "article_id": "art_2",
                    "headline": "Test Headline 2",
                    "body_blocks": [],
                },
            ],
        },
        "not_a_dict_page",
        {
            "page_number": 2,
            "articles": [
                "not_a_dict_article",
                {
                    "article_id": "art_3",
                    "headline": "Test Headline 3",
                    "body_blocks": ["Block 3"],
                },
            ],
        },
    ],
}


def test_export_jsonl_success(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")
    output_file = tmp_path / "output.jsonl"

    export_jsonl(input_file, output_file)

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 3
    data_1 = json.loads(lines[0])
    assert data_1["document_id"] == "test_doc"
    assert data_1["page_number"] == 1
    assert data_1["article_id"] == "art_1"
    assert data_1["headline"] == "Test Headline 1"
    assert data_1["body_blocks"] == ["Block 1", "Block 2"]

    data_2 = json.loads(lines[1])
    assert data_2["article_id"] == "art_2"
    assert data_2["body_blocks"] == []

    data_3 = json.loads(lines[2])
    assert data_3["page_number"] == 2
    assert data_3["article_id"] == "art_3"
    assert data_3["body_blocks"] == ["Block 3"]


def test_export_jsonl_same_path_error(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")

    with pytest.raises(ValueError, match="Input and output paths must be different."):
        export_jsonl(input_file, input_file)


def test_export_jsonl_invalid_format_error(tmp_path: Path) -> None:
    output_file = tmp_path / "output.jsonl"

    input_file_1 = tmp_path / "input1.json"
    input_file_1.write_text(json.dumps(["not a dict"]), encoding="utf-8")
    with pytest.raises(ValueError, match="NewsDOM JSON root must be an object."):
        export_jsonl(input_file_1, output_file)

    input_file_2 = tmp_path / "input2.json"
    input_file_2.write_text(json.dumps({"pages": "not a list"}), encoding="utf-8")
    with pytest.raises(ValueError, match="NewsDOM JSON field 'pages' must be a list."):
        export_jsonl(input_file_2, output_file)

    input_file_3 = tmp_path / "input3.json"
    input_file_3.write_text(
        json.dumps({"pages": [{"articles": "not a list"}]}), encoding="utf-8"
    )
    with pytest.raises(
        ValueError, match="NewsDOM page field 'articles' must be a list."
    ):
        export_jsonl(input_file_3, output_file)


def test_export_jsonl_invalid_file(tmp_path: Path) -> None:
    output_file = tmp_path / "output.jsonl"

    non_existent = tmp_path / "not_exist.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        export_jsonl(non_existent, output_file)

    not_json = tmp_path / "input.txt"
    not_json.write_text("plain text", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a .json file"):
        export_jsonl(not_json, output_file)

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{invalid_json:", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(invalid_json, output_file)


def test_export_jsonl_cli_success(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")
    output_file = tmp_path / "output.jsonl"

    main([str(input_file), str(output_file)])

    assert output_file.exists()
    captured = capsys.readouterr()
    assert "JSONL successfully written" in captured.out


def test_export_jsonl_cli_invalid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    not_json = tmp_path / "input.txt"
    not_json.write_text("plain text", encoding="utf-8")
    output_file = tmp_path / "output.jsonl"

    with pytest.raises(SystemExit) as exc_info:
        main([str(not_json), str(output_file)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL:" in captured.err


def test_export_jsonl_preserves_published_output_when_encoding_fails(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")
    output_file = tmp_path / "output.jsonl"

    # Create an initial output file
    output_file.write_text("original data", encoding="utf-8")

    # Mock json.dumps to raise a UnicodeEncodeError
    with patch(
        "json.dumps", side_effect=UnicodeEncodeError("utf-8", "", 0, 1, "mock error")
    ):
        with pytest.raises(UnicodeEncodeError):
            export_jsonl(input_file, output_file)

    # Check that original file was preserved
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == "original data"

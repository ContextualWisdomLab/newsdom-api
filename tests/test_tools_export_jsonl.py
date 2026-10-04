from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.export_jsonl import export_jsonl, main, _strict_parse_constant

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
    art1 = json.loads(lines[0])
    assert art1["document_id"] == "test_doc"
    assert art1["page_number"] == 1
    assert art1["article_id"] == "art_1"

    art2 = json.loads(lines[1])
    assert art2["document_id"] == "test_doc"
    assert art2["page_number"] == 1
    assert art2["article_id"] == "art_2"

    art3 = json.loads(lines[2])
    assert art3["document_id"] == "test_doc"
    assert art3["page_number"] == 2
    assert art3["article_id"] == "art_3"


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

    bad_root_json = tmp_path / "bad_root.json"
    bad_root_json.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="Root JSON object must be a dictionary"):
        export_jsonl(bad_root_json, output_file)

    same_path_json = tmp_path / "same.json"
    same_path_json.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Input and output paths cannot be the same file"):
        export_jsonl(same_path_json, same_path_json)


def test_export_jsonl_strict_parse(tmp_path: Path) -> None:
    output_file = tmp_path / "output.jsonl"
    nan_json = tmp_path / "nan.json"
    nan_json.write_text('{"val": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file: Invalid non-standard JSON float"):
        export_jsonl(nan_json, output_file)


def test_export_jsonl_strict_write(tmp_path: Path) -> None:
    output_file = tmp_path / "output.jsonl"
    input_file = tmp_path / "input.json"
    import math
    data = {"pages": [{"articles": [{"val": math.nan}]}]}
    # Don't use allow_nan=True, just write normal JSON, bypass validation with literal string
    input_file.write_text('{"pages": [{"articles": [{"val": 1.0}]}]}', encoding="utf-8")

    # Actually we just want to test if it raises when saving.
    # To bypass load-time check, we need valid json in input, but somehow insert NaN before save.
    # Since export_jsonl reads and writes immediately, we can't easily mock the read data without patching json.loads.
    with patch('json.loads', return_value={"pages": [{"articles": [{"val": math.nan}]}]}):
        with pytest.raises(ValueError, match="Out of range float values are not JSON compliant"):
            export_jsonl(input_file, output_file)


def test_export_jsonl_cli_success(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")
    output_file = tmp_path / "output.jsonl"

    with patch("sys.argv", ["export_jsonl", str(input_file), str(output_file)]):
        main()

    assert output_file.exists()
    captured = capsys.readouterr()
    assert "JSONL successfully written" in captured.out


def test_export_jsonl_cli_invalid_file(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    not_json = tmp_path / "input.txt"
    not_json.write_text("plain text", encoding="utf-8")
    output_file = tmp_path / "output.jsonl"

    with patch("sys.argv", ["export_jsonl", str(not_json), str(output_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL:" in captured.err


def test_export_jsonl_bad_pages_and_articles(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    # Test when pages is not list, or articles is not list
    bad_pages_data = {
        "pages": "not_a_list",
        "document_id": "test"
    }
    input_file.write_text(json.dumps(bad_pages_data), encoding="utf-8")
    output_file = tmp_path / "output.jsonl"
    export_jsonl(input_file, output_file)
    assert output_file.read_text() == ""

    bad_articles_data = {
        "pages": [
            {"articles": "not_a_list"}
        ]
    }
    input_file.write_text(json.dumps(bad_articles_data), encoding="utf-8")
    export_jsonl(input_file, output_file)
    assert output_file.read_text() == ""

from __future__ import annotations

import json
from pathlib import Path
import unittest.mock

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
        {
            "page_number": 2,
            "articles": [
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
        lines = f.read().splitlines()

        assert len(lines) == 3

        row0 = json.loads(lines[0])
        assert row0["document_id"] == "test_doc"
        assert row0["page_number"] == 1
        assert row0["article"]["article_id"] == "art_1"
        assert row0["article"]["headline"] == "Test Headline 1"

        row1 = json.loads(lines[1])
        assert row1["article"]["article_id"] == "art_2"
        assert row1["article"]["headline"] == "Test Headline 2"

        row2 = json.loads(lines[2])
        assert row2["page_number"] == 2
        assert row2["article"]["article_id"] == "art_3"


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

    invalid_schema = tmp_path / "invalid_schema.json"
    invalid_schema.write_text(
        json.dumps({"pages": ["not_a_dict_page"]}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Invalid JSON schema"):
        export_jsonl(invalid_schema, output_file)


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
    output_file.write_text("original content", encoding="utf-8")

    with unittest.mock.patch(
        "tools.export_jsonl.json.dumps", side_effect=TypeError("Not serializable")
    ):
        with pytest.raises(TypeError):
            export_jsonl(input_file, output_file)

    assert output_file.read_text(encoding="utf-8") == "original content"

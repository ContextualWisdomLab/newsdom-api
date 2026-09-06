from __future__ import annotations

import json
from pathlib import Path

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
    output_file = tmp_path / "nested" / "output.jsonl"

    export_jsonl(input_file, output_file)

    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3

    row1 = json.loads(lines[0])
    assert row1 == {
        "document_id": "test_doc",
        "page_number": 1,
        "article_id": "art_1",
        "headline": "Test Headline 1",
        "body_blocks": ["Block 1", "Block 2"],
    }

    row2 = json.loads(lines[1])
    assert row2["headline"] == "Test Headline 2"
    assert row2["body_blocks"] == []

    row3 = json.loads(lines[2])
    assert row3["page_number"] == 2
    assert row3["article_id"] == "art_3"
    assert row3["body_blocks"] == ["Block 3"]


def test_export_jsonl_rejects_noncanonical_newsdom(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    malformed = {
        **VALID_JSON_DATA,
        "pages": [{"page_number": 1, "articles": ["not-an-article"]}],
    }
    input_file.write_text(json.dumps(malformed), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        export_jsonl(input_file, tmp_path / "output.jsonl")


def test_export_jsonl_rejects_input_as_output_without_modifying_source(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "input.json"
    original = json.dumps(VALID_JSON_DATA)
    input_file.write_text(original, encoding="utf-8")

    with pytest.raises(ValueError, match="must differ from input"):
        export_jsonl(input_file, input_file)

    assert input_file.read_text(encoding="utf-8") == original


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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")
    output_file = tmp_path / "output.jsonl"

    main([str(input_file), str(output_file)])

    assert output_file.exists()
    captured = capsys.readouterr()
    assert "JSONL successfully written" in captured.out


def test_export_jsonl_cli_invalid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    not_json = tmp_path / "input.txt"
    not_json.write_text("plain text", encoding="utf-8")
    output_file = tmp_path / "output.jsonl"

    with pytest.raises(SystemExit) as exc_info:
        main([str(not_json), str(output_file)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL:" in captured.err

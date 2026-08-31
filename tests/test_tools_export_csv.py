from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from tools.export_csv import export_csv, main

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


def test_export_csv_success(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")
    output_file = tmp_path / "output.csv"

    export_csv(input_file, output_file)

    assert output_file.exists()

    with output_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        assert len(rows) == 4
        assert rows[0]["document_id"] == "test_doc"
        assert rows[0]["page_number"] == "1"
        assert rows[0]["article_id"] == "art_1"
        assert rows[0]["headline"] == "Test Headline 1"
        assert rows[0]["body_block_index"] == "0"
        assert rows[0]["body_block_text"] == "Block 1"

        assert rows[1]["body_block_index"] == "1"
        assert rows[1]["body_block_text"] == "Block 2"

        assert rows[2]["headline"] == "Test Headline 2"
        assert rows[2]["body_block_index"] == ""
        assert rows[2]["body_block_text"] == ""

        assert rows[3]["page_number"] == "2"
        assert rows[3]["article_id"] == "art_3"
        assert rows[3]["body_block_index"] == "0"
        assert rows[3]["body_block_text"] == "Block 3"


def test_export_csv_invalid_file(tmp_path: Path) -> None:
    output_file = tmp_path / "output.csv"

    non_existent = tmp_path / "not_exist.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        export_csv(non_existent, output_file)

    not_json = tmp_path / "input.txt"
    not_json.write_text("plain text", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a .json file"):
        export_csv(not_json, output_file)

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{invalid_json:", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_csv(invalid_json, output_file)


def test_export_csv_cli_success(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")
    output_file = tmp_path / "output.csv"

    main([str(input_file), str(output_file)])

    assert output_file.exists()
    captured = capsys.readouterr()
    assert "CSV successfully written" in captured.out


def test_export_csv_cli_invalid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    not_json = tmp_path / "input.txt"
    not_json.write_text("plain text", encoding="utf-8")
    output_file = tmp_path / "output.csv"

    with pytest.raises(SystemExit) as exc_info:
        main([str(not_json), str(output_file)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting CSV:" in captured.err


def test_module_main() -> None:
    import runpy
    import sys
    from unittest.mock import patch

    sys.modules.pop("tools.export_csv", None)
    with patch("sys.argv", ["tools/export_csv.py", "-h"]):
        try:
            runpy.run_module("tools.export_csv", run_name="__main__")
        except SystemExit as excinfo:
            assert excinfo.code == 0

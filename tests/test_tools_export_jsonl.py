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

        record1 = json.loads(lines[0])
        assert record1["document_id"] == "test_doc"
        assert record1["page_number"] == 1
        assert record1["article_id"] == "art_1"
        assert record1["headline"] == "Test Headline 1"
        assert record1["body_blocks"] == ["Block 1", "Block 2"]

        record2 = json.loads(lines[1])
        assert record2["article_id"] == "art_2"
        assert record2["headline"] == "Test Headline 2"
        assert record2["body_blocks"] == []

        record3 = json.loads(lines[2])
        assert record3["page_number"] == 2
        assert record3["article_id"] == "art_3"
        assert record3["body_blocks"] == ["Block 3"]


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


def test_export_jsonl_cli_success(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
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


def test_export_jsonl_preserves_published_output_when_encoding_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Test atomic writing to prevent data loss on failure
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")

    output_file = tmp_path / "output.jsonl"
    original_content = '{"existing": "data"}\n'
    output_file.write_text(original_content, encoding="utf-8")

    # Mock json.dumps to raise an exception during processing
    def mock_dumps(*args, **kwargs):
        raise TypeError("Object of type XXX is not JSON serializable")

    monkeypatch.setattr(json, "dumps", mock_dumps)

    with pytest.raises(TypeError):
        export_jsonl(input_file, output_file)

    # The original file should be unmodified
    assert output_file.read_text(encoding="utf-8") == original_content

def test_export_jsonl_temp_file_not_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Test error handling when NamedTemporaryFile fails
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")

    output_file = tmp_path / "output.jsonl"

    # Mock NamedTemporaryFile to raise an exception before temp_path is defined
    def mock_named_temporary_file(*args, **kwargs):
        raise OSError("Permission denied")

    import tools.export_jsonl
    monkeypatch.setattr(tools.export_jsonl, "NamedTemporaryFile", mock_named_temporary_file)

    with pytest.raises(OSError, match="Permission denied"):
        export_jsonl(input_file, output_file)

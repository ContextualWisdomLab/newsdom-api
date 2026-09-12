from __future__ import annotations

import json
import tempfile
from copy import deepcopy
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
        {
            "page_number": 2,
            "articles": [
                {
                    "article_id": "art_3",
                    "headline": "Test Headline 3",
                    "body_blocks": ["Block 3"],
                }
            ],
        },
    ],
}


def _write_input(tmp_path: Path, payload: object) -> Path:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(payload), encoding="utf-8")
    return input_file


def test_export_jsonl_success(tmp_path: Path) -> None:
    input_file = _write_input(tmp_path, VALID_JSON_DATA)
    output_file = tmp_path / "output.jsonl"

    export_jsonl(input_file, output_file)

    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 4

    row0 = json.loads(lines[0])
    assert row0["document_id"] == "test_doc"
    assert row0["page_number"] == 1
    assert row0["article_id"] == "art_1"
    assert row0["headline"] == "Test Headline 1"
    assert row0["body_block_index"] == 0
    assert row0["body_block_text"] == "Block 1"

    row1 = json.loads(lines[1])
    assert row1["body_block_index"] == 1
    assert row1["body_block_text"] == "Block 2"

    row2 = json.loads(lines[2])
    assert row2["headline"] == "Test Headline 2"
    assert row2["body_block_index"] == ""
    assert row2["body_block_text"] == ""

    row3 = json.loads(lines[3])
    assert row3["page_number"] == 2
    assert row3["article_id"] == "art_3"
    assert row3["body_block_index"] == 0
    assert row3["body_block_text"] == "Block 3"


def test_export_jsonl_invalid_file(tmp_path: Path) -> None:
    output_file = tmp_path / "output.jsonl"

    non_existent = tmp_path / "not_exist.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        export_jsonl(non_existent, output_file)

    not_json = tmp_path / "input.txt"
    not_json.write_text("plain text", encoding="utf-8")
    with pytest.raises(ValueError, match=r"must be a \.json file"):
        export_jsonl(not_json, output_file)

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{invalid_json:", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(invalid_json, output_file)


def test_export_jsonl_rejects_non_object_page_before_publish(tmp_path: Path) -> None:
    payload = deepcopy(VALID_JSON_DATA)
    payload["pages"].append("not-a-page")
    input_file = _write_input(tmp_path, payload)
    output_file = tmp_path / "output.jsonl"
    output_file.write_text("published\n", encoding="utf-8")

    with pytest.raises(ValueError, match="valid NewsDOM parse response"):
        export_jsonl(input_file, output_file)

    assert output_file.read_text(encoding="utf-8") == "published\n"


def test_export_jsonl_rejects_non_object_article_before_publish(tmp_path: Path) -> None:
    payload = deepcopy(VALID_JSON_DATA)
    payload["pages"][0]["articles"].append("not-an-article")
    input_file = _write_input(tmp_path, payload)
    output_file = tmp_path / "output.jsonl"
    output_file.write_text("published\n", encoding="utf-8")

    with pytest.raises(ValueError, match="valid NewsDOM parse response"):
        export_jsonl(input_file, output_file)

    assert output_file.read_text(encoding="utf-8") == "published\n"


def test_export_jsonl_rejects_non_list_body_blocks_before_publish(tmp_path: Path) -> None:
    payload = deepcopy(VALID_JSON_DATA)
    payload["pages"][0]["articles"][0]["body_blocks"] = "not-a-list"
    input_file = _write_input(tmp_path, payload)
    output_file = tmp_path / "output.jsonl"
    output_file.write_text("published\n", encoding="utf-8")

    with pytest.raises(ValueError, match="valid NewsDOM parse response"):
        export_jsonl(input_file, output_file)

    assert output_file.read_text(encoding="utf-8") == "published\n"


def test_export_jsonl_rejects_missing_required_article_identity(tmp_path: Path) -> None:
    payload = deepcopy(VALID_JSON_DATA)
    del payload["pages"][0]["articles"][0]["article_id"]
    input_file = _write_input(tmp_path, payload)
    output_file = tmp_path / "output.jsonl"

    with pytest.raises(ValueError, match="valid NewsDOM parse response"):
        export_jsonl(input_file, output_file)

    assert not output_file.exists()


def test_export_jsonl_creates_temp_file_in_output_directory(tmp_path: Path) -> None:
    input_file = _write_input(tmp_path, VALID_JSON_DATA)
    output_dir = tmp_path / "published"
    output_dir.mkdir()
    output_file = output_dir / "output.jsonl"
    original_named_temporary_file = tempfile.NamedTemporaryFile
    observed_dir: Path | None = None

    def named_temporary_file(*args, **kwargs):
        nonlocal observed_dir
        directory = kwargs.get("dir")
        observed_dir = Path(directory) if directory is not None else None
        return original_named_temporary_file(*args, **kwargs)

    with patch(
        "tools.export_jsonl.tempfile.NamedTemporaryFile",
        side_effect=named_temporary_file,
    ):
        export_jsonl(input_file, output_file)

    assert observed_dir == output_file.parent


def test_export_jsonl_cli_success(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    input_file = _write_input(tmp_path, VALID_JSON_DATA)
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
    input_file = _write_input(tmp_path, VALID_JSON_DATA)
    output_file = tmp_path / "output.jsonl"
    original_content = "existing content that should not be deleted"
    output_file.write_text(original_content, encoding="utf-8")

    with patch(
        "tools.export_jsonl.json.dumps", side_effect=TypeError("mock encoding error")
    ):
        with pytest.raises(TypeError, match="mock encoding error"):
            export_jsonl(input_file, output_file)

    assert output_file.read_text(encoding="utf-8") == original_content


def test_export_jsonl_preserves_original_exception_when_cleanup_fails(
    tmp_path: Path,
) -> None:
    input_file = _write_input(tmp_path, VALID_JSON_DATA)
    output_file = tmp_path / "output.jsonl"

    with patch("tools.export_jsonl.json.dumps", side_effect=TypeError("mock error")):
        with patch("pathlib.Path.unlink", side_effect=OSError("mock unlink error")):
            with pytest.raises(TypeError, match="mock error"):
                export_jsonl(input_file, output_file)


def test_export_jsonl_tempfile_creation_fails(tmp_path: Path) -> None:
    input_file = _write_input(tmp_path, VALID_JSON_DATA)
    output_file = tmp_path / "output.jsonl"

    with patch(
        "tools.export_jsonl.tempfile.NamedTemporaryFile",
        side_effect=OSError("mock tempfile error"),
    ):
        with pytest.raises(OSError, match="mock tempfile error"):
            export_jsonl(input_file, output_file)

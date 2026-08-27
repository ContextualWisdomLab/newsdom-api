from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.export_jsonl import export_jsonl, main

VALID_JSON_DATA = {
    "document_id": "doc1",
    "pages": [
        {
            "page_number": 1,
            "articles": [
                {
                    "article_id": "art_1",
                    "headline": "Head1",
                    "body_blocks": ["Block 1", "Block 2"],
                }
            ],
        },
        "not_a_dict_page",
        {
            "page_number": 2,
            "articles": [
                "not_a_dict_article",
                {"article_id": "art_2", "headline": "Head2", "body_blocks": []},
            ],
        },
    ],
}


def test_export_jsonl_success(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "file1.json").write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")

    sub_dir = input_dir / "sub"
    sub_dir.mkdir()
    (sub_dir / "file2.json").write_text(
        json.dumps(
            {
                "document_id": "doc2",
                "pages": [{"page_number": 3, "articles": [{"article_id": "art_3"}]}],
            }
        ),
        encoding="utf-8",
    )

    output_file = tmp_path / "output.jsonl"

    # Non-recursive
    export_jsonl(input_dir, output_file)
    assert output_file.exists()

    lines = output_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2

    doc = json.loads(lines[0])
    assert doc["document_id"] == "doc1"
    assert doc["article_id"] == "art_1"

    # Recursive
    export_jsonl(input_dir, output_file, recursive=True)
    lines = output_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3


def test_export_jsonl_invalid_input(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    output_file = tmp_path / "output.jsonl"

    with pytest.raises(FileNotFoundError, match="No JSON files found in"):
        export_jsonl(input_dir, output_file)

    (input_dir / "invalid.json").write_text("{invalid json", encoding="utf-8")
    (input_dir / "valid.json").write_text(
        json.dumps(
            {
                "document_id": "doc3",
                "pages": [{"page_number": 1, "articles": [{"article_id": "art_x"}]}],
            }
        ),
        encoding="utf-8",
    )

    export_jsonl(input_dir, output_file)

    captured = capsys.readouterr()
    assert "Skipping invalid JSON file invalid.json" in captured.err

    lines = output_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    assert json.loads(lines[0])["document_id"] == "doc3"

    with pytest.raises(NotADirectoryError, match="Input is not a directory:"):
        export_jsonl(tmp_path / "not_exist", output_file)


def test_main_success(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "file1.json").write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")

    output_file = tmp_path / "output.jsonl"

    main([str(input_dir), str(output_file)])

    captured = capsys.readouterr()
    assert "JSONL successfully written to" in captured.out
    assert output_file.exists()


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    input_dir = tmp_path / "not_exist"
    output_file = tmp_path / "output.jsonl"

    with pytest.raises(SystemExit) as exc_info:
        main([str(input_dir), str(output_file)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Input is not a directory:" in captured.err

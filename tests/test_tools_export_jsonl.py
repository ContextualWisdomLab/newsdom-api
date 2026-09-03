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
    output_file = tmp_path / "output.jsonl"

    export_jsonl(input_file, output_file)

    assert output_file.exists()

    lines = output_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3

    art1 = json.loads(lines[0])
    assert art1["document_id"] == "test_doc"
    assert art1["page_number"] == 1
    assert art1["article_id"] == "art_1"
    assert art1["headline"] == "Test Headline 1"
    assert art1["body_blocks"] == ["Block 1", "Block 2"]

    art2 = json.loads(lines[1])
    assert art2["article_id"] == "art_2"
    assert art2["headline"] == "Test Headline 2"
    assert art2["body_blocks"] == []

    art3 = json.loads(lines[2])
    assert art3["page_number"] == 2
    assert art3["article_id"] == "art_3"
    assert art3["headline"] == "Test Headline 3"
    assert art3["body_blocks"] == ["Block 3"]


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


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "top-level JSON value must be an object"),
        ({"pages": {}}, "pages must be a list"),
        ({"pages": ["bad-page"]}, "page at index 0 must be an object"),
        (
            {"pages": [{"articles": "bad-articles"}]},
            "articles for page index 0 must be a list",
        ),
        (
            {"pages": [{"articles": ["bad-article"]}]},
            "article at page index 0, index 0 must be an object",
        ),
    ],
)
def test_export_jsonl_rejects_malformed_newsdom_structure(
    tmp_path: Path, payload: object, message: str
) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(payload), encoding="utf-8")
    output_file = tmp_path / "output.jsonl"

    with pytest.raises(ValueError, match=message):
        export_jsonl(input_file, output_file)

    assert not output_file.exists()


def test_export_jsonl_validation_failure_preserves_existing_output(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(
        json.dumps({"pages": [{"articles": ["bad-article"]}]}),
        encoding="utf-8",
    )
    output_file = tmp_path / "output.jsonl"
    output_file.write_text("previous-good-output\n", encoding="utf-8")

    with pytest.raises(ValueError, match="article at page index 0, index 0"):
        export_jsonl(input_file, output_file)

    assert output_file.read_text(encoding="utf-8") == "previous-good-output\n"


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

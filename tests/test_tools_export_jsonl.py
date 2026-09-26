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

        art_1 = json.loads(lines[0])
        assert art_1["article_id"] == "art_1"
        assert art_1["headline"] == "Test Headline 1"
        assert art_1["body_blocks"] == ["Block 1", "Block 2"]

        art_2 = json.loads(lines[1])
        assert art_2["article_id"] == "art_2"

        art_3 = json.loads(lines[2])
        assert art_3["article_id"] == "art_3"


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

    invalid_top_level = tmp_path / "invalid_top.json"
    invalid_top_level.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="Top-level JSON must be a dictionary."):
        export_jsonl(invalid_top_level, output_file)


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


def test_export_jsonl_invalid_pages_list(tmp_path: Path) -> None:
    output_file = tmp_path / "output.jsonl"
    invalid_json = tmp_path / "invalid_pages.json"

    # Test when 'pages' is not a list (e.g. integer)
    invalid_json.write_text('{"pages": 1}', encoding="utf-8")
    export_jsonl(invalid_json, output_file)
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == ""

    # Test when 'articles' is not a list (e.g. string)
    invalid_json.write_text('{"pages": [{"articles": "not_a_list"}]}', encoding="utf-8")
    export_jsonl(invalid_json, output_file)
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == ""


def test_export_jsonl_invalid_number_constants(tmp_path: Path) -> None:
    output_file = tmp_path / "output.jsonl"
    invalid_json = tmp_path / "invalid_nan.json"

    # Test when input contains NaN or Infinity
    invalid_json.write_text('{"pages": [{"articles": [{"val": NaN}]}]}', encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(invalid_json, output_file)


def test_export_jsonl_adds_provenance(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"

    input_data = {
        "document_id": "prov_doc",
        "pages": [
            {
                "page_number": 42,
                "articles": [
                    {
                        "article_id": "prov_art",
                        "headline": "Prov Headline"
                    }
                ]
            }
        ]
    }
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    export_jsonl(input_file, output_file)

    with output_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        art = json.loads(lines[0])
        assert art["document_id"] == "prov_doc"
        assert art["page_number"] == 42


def test_export_jsonl_provenance_edge_cases(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"

    input_data = {
        "document_id": "root_doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art_1",
                        "document_id": "existing_doc",
                        "page_number": 99
                    }
                ]
            },
            {
                "articles": [
                    {
                        "article_id": "art_2"
                    }
                ]
            }
        ]
    }
    # For art_2, document_id gets added, but there is no page_number in parent.

    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    export_jsonl(input_file, output_file)

    with output_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 2
        art1 = json.loads(lines[0])
        assert art1["document_id"] == "existing_doc"
        assert art1["page_number"] == 99

        art2 = json.loads(lines[1])
        assert art2["document_id"] == "root_doc"
        assert "page_number" not in art2

from __future__ import annotations

import json
from pathlib import Path

import pytest
from unittest.mock import patch

from tools.export_jsonl import export_jsonl, _strict_float, main

VALID_JSON_DATA = {
    "document_id": "test_doc",
    "pages": [
        {
            "page_number": 1,
            "articles": [
                {
                    "article_id": "art_1",
                    "headline": "Test 1"
                }
            ]
        },
        "not_a_dict",
        {
            "page_number": 2,
            "articles": "not_a_list"
        },
        {
            "page_number": 3,
            "articles": [
                "not_a_dict"
            ]
        }
    ]
}


def test_export_jsonl_success(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")
    output_file = tmp_path / "output.jsonl"

    export_jsonl(input_file, output_file)

    assert output_file.exists()
    lines = output_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["document_id"] == "test_doc"
    assert data["page_number"] == 1
    assert data["article_id"] == "art_1"


def test_export_jsonl_same_path(tmp_path: Path) -> None:
    f = tmp_path / "test.json"
    f.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Input and output paths must not be the same"):
        export_jsonl(f, f)


def test_export_jsonl_invalid_float(tmp_path: Path) -> None:
    f = tmp_path / "input.json"
    f.write_text("{\"val\": NaN}", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="Invalid float"):
        export_jsonl(f, out)


def test_export_jsonl_invalid_json(tmp_path: Path) -> None:
    f = tmp_path / "input.json"
    f.write_text("{invalid", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(f, out)


def test_export_jsonl_invalid_encoding(tmp_path: Path) -> None:
    f = tmp_path / "input.json"
    f.write_bytes(b"\xff\xfe")
    out = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="Invalid JSON encoding"):
        export_jsonl(f, out)


def test_export_jsonl_non_dict(tmp_path: Path) -> None:
    f = tmp_path / "input.json"
    f.write_text("[]", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="Top-level JSON must be a dictionary"):
        export_jsonl(f, out)


def test_strict_float() -> None:
    assert _strict_float("1.23") == 1.23
    with pytest.raises(ValueError, match="Non-finite float"):
        _strict_float("NaN")


def test_export_jsonl_cli_success(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    f = tmp_path / "input.json"
    f.write_text(json.dumps(VALID_JSON_DATA), encoding="utf-8")
    out = tmp_path / "out.jsonl"
    main([str(f), str(out)])
    assert "successfully written" in capsys.readouterr().out


def test_export_jsonl_cli_error(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    f = tmp_path / "input.json"
    out = tmp_path / "out.jsonl"
    with pytest.raises(SystemExit) as exc:
        main([str(f), str(out)])
    assert exc.value.code == 1
    assert "Error exporting JSONL" in capsys.readouterr().err

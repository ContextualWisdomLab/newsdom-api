import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.export_jsonl import export_jsonl, main, _reject_non_finite

def test_reject_non_finite():
    with pytest.raises(ValueError, match="Non-standard float token"):
        _reject_non_finite("NaN")

def test_export_jsonl_success(tmp_path):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"

    data = {
        "document_id": "doc-123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"article_id": "art-1", "headline": "Headline 1", "body_blocks": ["Block 1"]},
                    {"article_id": "art-2", "headline": "Headline 2", "body_blocks": ["Block 2", "Block 3"]}
                ]
            },
            {
                "page_number": 2,
                "articles": [
                    {"article_id": "art-3", "headline": "Headline 3", "body_blocks": []}
                ]
            }
        ]
    }

    input_json.write_text(json.dumps(data), encoding="utf-8")

    export_jsonl(input_json, output_jsonl)

    assert output_jsonl.exists()

    lines = output_jsonl.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3

    art1 = json.loads(lines[0])
    assert art1["document_id"] == "doc-123"
    assert art1["page_number"] == 1
    assert art1["article_id"] == "art-1"

    art2 = json.loads(lines[1])
    assert art2["document_id"] == "doc-123"
    assert art2["page_number"] == 1
    assert art2["article_id"] == "art-2"

    art3 = json.loads(lines[2])
    assert art3["document_id"] == "doc-123"
    assert art3["page_number"] == 2
    assert art3["article_id"] == "art-3"

def test_export_jsonl_empty_pages(tmp_path):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"

    data = {"document_id": "doc-123", "pages": []}
    input_json.write_text(json.dumps(data), encoding="utf-8")

    export_jsonl(input_json, output_jsonl)

    assert output_jsonl.exists()
    assert output_jsonl.read_text(encoding="utf-8") == ""

def test_export_jsonl_invalid_json(tmp_path):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"

    input_json.write_text("{invalid json}", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(input_json, output_jsonl)

def test_export_jsonl_non_finite_float(tmp_path):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"

    input_json.write_text('{"val": NaN}', encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON data"):
        export_jsonl(input_json, output_jsonl)

def test_export_jsonl_same_file(tmp_path):
    input_json = tmp_path / "input.json"
    input_json.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="same file"):
        export_jsonl(input_json, input_json)

def test_export_jsonl_file_not_found(tmp_path):
    input_json = tmp_path / "nonexistent.json"
    output_jsonl = tmp_path / "output.jsonl"

    with pytest.raises(FileNotFoundError):
        export_jsonl(input_json, output_jsonl)

def test_export_jsonl_bad_encoding(tmp_path):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"

    input_json.write_bytes(b"\x80\x81")

    with pytest.raises(ValueError, match="Invalid encoding"):
        export_jsonl(input_json, output_jsonl)

def test_main_success(tmp_path, capsys):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"

    data = {"document_id": "doc-123", "pages": []}
    input_json.write_text(json.dumps(data), encoding="utf-8")

    with patch("sys.argv", ["export_jsonl.py", str(input_json), str(output_jsonl)]):
        main()

    captured = capsys.readouterr()
    assert "successfully written" in captured.out
    assert output_jsonl.exists()

def test_main_error(tmp_path, capsys):
    input_json = tmp_path / "nonexistent.json"
    output_jsonl = tmp_path / "output.jsonl"

    with patch("sys.argv", ["export_jsonl.py", str(input_json), str(output_jsonl)]):
        with pytest.raises(SystemExit) as excinfo:
            main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL" in captured.err

def test_export_jsonl_page_not_dict(tmp_path):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"

    data = {
        "document_id": "doc-123",
        "pages": [
            "not a dict",
            {
                "page_number": 1,
                "articles": [
                    {"article_id": "art-1", "headline": "Headline 1", "body_blocks": ["Block 1"]}
                ]
            }
        ]
    }
    input_json.write_text(json.dumps(data), encoding="utf-8")

    export_jsonl(input_json, output_jsonl)

    assert output_jsonl.exists()
    lines = output_jsonl.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

def test_export_jsonl_article_not_dict(tmp_path):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"

    data = {
        "document_id": "doc-123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    "not a dict",
                    {"article_id": "art-1", "headline": "Headline 1", "body_blocks": ["Block 1"]}
                ]
            }
        ]
    }
    input_json.write_text(json.dumps(data), encoding="utf-8")

    export_jsonl(input_json, output_jsonl)

    assert output_jsonl.exists()
    lines = output_jsonl.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

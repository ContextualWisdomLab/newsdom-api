import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.export_jsonl import export_jsonl, main

def test_export_jsonl_success(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"

    data = {
        "document_id": "doc_123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"article_id": "a1", "headline": "A"},
                    {"article_id": "a2", "headline": "B"}
                ]
            },
            {
                "page_number": 2,
                "articles": [
                    {"article_id": "a3", "headline": "C"}
                ]
            }
        ]
    }
    input_file.write_text(json.dumps(data), encoding="utf-8")

    export_jsonl(input_file, output_file)

    assert output_file.exists()
    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3

    obj1 = json.loads(lines[0])
    assert obj1["article_id"] == "a1"
    assert obj1["document_id"] == "doc_123"
    assert obj1["page_number"] == 1

    obj3 = json.loads(lines[2])
    assert obj3["article_id"] == "a3"
    assert obj3["document_id"] == "doc_123"
    assert obj3["page_number"] == 2

def test_export_jsonl_same_file(tmp_path: Path):
    input_file = tmp_path / "input.json"
    input_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="same file"):
        export_jsonl(input_file, input_file)

def test_export_jsonl_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        export_jsonl(tmp_path / "not_found.json", tmp_path / "out.jsonl")

def test_export_jsonl_invalid_json(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        export_jsonl(input_file, output_file)

def test_export_jsonl_non_finite_float(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text('{"val": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON|Non-standard float"):
        export_jsonl(input_file, output_file)

def test_export_jsonl_top_level_not_dict(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="Top-level JSON structure must be a dictionary"):
        export_jsonl(input_file, output_file)

def test_export_jsonl_main(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text('{"document_id": "1", "pages": []}', encoding="utf-8")
    main([str(input_file), str(output_file)])
    assert output_file.exists()

def test_export_jsonl_main_error(tmp_path: Path):
    with patch("sys.stderr"):
        with pytest.raises(SystemExit) as excinfo:
            main([str(tmp_path / "not_found.json"), str(tmp_path / "out.jsonl")])
        assert excinfo.value.code == 1

def test_export_jsonl_unicode_decode_error(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_bytes(b"\x80abc")
    with pytest.raises(ValueError, match="File encoding error"):
        export_jsonl(input_file, output_file)

def test_export_jsonl_pages_not_list(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text('{"document_id": "1", "pages": {}}', encoding="utf-8")
    export_jsonl(input_file, output_file)
    assert output_file.exists()

def test_export_jsonl_page_not_dict(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text('{"document_id": "1", "pages": ["not a dict"]}', encoding="utf-8")
    export_jsonl(input_file, output_file)
    assert output_file.exists()

def test_export_jsonl_articles_not_list(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text('{"document_id": "1", "pages": [{"articles": "not a list"}]}', encoding="utf-8")
    export_jsonl(input_file, output_file)
    assert output_file.exists()

def test_export_jsonl_article_not_dict(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text('{"document_id": "1", "pages": [{"articles": ["not a dict"]}]}', encoding="utf-8")
    export_jsonl(input_file, output_file)
    assert output_file.exists()

def test_export_jsonl_no_provenance(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text('{"pages": [{"articles": [{"article_id": "1"}]}]}', encoding="utf-8")
    export_jsonl(input_file, output_file)
    assert output_file.exists()

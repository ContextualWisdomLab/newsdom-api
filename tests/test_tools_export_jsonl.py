import json
import os
import sys
import unittest.mock
from pathlib import Path
import pytest
from tools.export_jsonl import export_jsonl, main

def test_export_jsonl_success(tmp_path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.jsonl"
    data = {"document_id": "doc_1", "pages": [{"page_number": 1, "articles": [{"article_id": "a1", "headline": "Title 1"}]}]}
    input_path.write_text(json.dumps(data), encoding="utf-8")
    export_jsonl(input_path, output_path)
    lines = output_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    res = json.loads(lines[0])
    assert res["document_id"] == "doc_1"
    assert res["page_number"] == 1
    assert res["article_id"] == "a1"

def test_export_jsonl_invalid_input_path(tmp_path):
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(FileNotFoundError):
        export_jsonl(tmp_path / "missing.json", output_path)

def test_export_jsonl_invalid_suffix(tmp_path):
    input_path = tmp_path / "input.txt"
    input_path.write_text("{}", encoding="utf-8")
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(ValueError, match="must be a .json file"):
        export_jsonl(input_path, output_path)

def test_export_jsonl_same_file(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Input and output paths must not be the same file."):
        export_jsonl(input_path, input_path)

def test_export_jsonl_samefile_os(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text("{}", encoding="utf-8")
    output_path = tmp_path / "symlink.json"
    old_dir = os.getcwd()
    os.chdir(tmp_path)
    os.symlink("input.json", "symlink.json")
    os.chdir(old_dir)
    with pytest.raises(ValueError, match="Input and output paths must not be the same file."):
        export_jsonl(input_path, output_path)

def test_export_jsonl_invalid_json(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text("{", encoding="utf-8")
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(input_path, output_path)

def test_export_jsonl_nan_value(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text('{"val": NaN}', encoding="utf-8")
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(ValueError, match="Invalid JSON content"):
        export_jsonl(input_path, output_path)

def test_export_jsonl_not_dict(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text("[]", encoding="utf-8")
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(ValueError, match="Top-level JSON must be a dictionary"):
        export_jsonl(input_path, output_path)

def test_export_jsonl_bad_pages(tmp_path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.jsonl"
    input_path.write_text('{"pages": {}}', encoding="utf-8")
    export_jsonl(input_path, output_path)
    assert output_path.read_text(encoding="utf-8") == ""
    input_path.write_text('{"pages": ["not dict"]}', encoding="utf-8")
    export_jsonl(input_path, output_path)
    assert output_path.read_text(encoding="utf-8") == ""
    input_path.write_text('{"pages": [{"articles": {}}]}', encoding="utf-8")
    export_jsonl(input_path, output_path)
    assert output_path.read_text(encoding="utf-8") == ""
    input_path.write_text('{"pages": [{"articles": ["not dict"]}]}', encoding="utf-8")
    export_jsonl(input_path, output_path)
    assert output_path.read_text(encoding="utf-8") == ""

def test_main_success(tmp_path, capsys):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.jsonl"
    input_path.write_text('{"document_id": "test"}', encoding="utf-8")
    with unittest.mock.patch("sys.argv", ["export_jsonl.py", str(input_path), str(output_path)]):
        main()
    captured = capsys.readouterr()
    assert "successfully written" in captured.out

def test_main_error(tmp_path, capsys):
    input_path = tmp_path / "missing.json"
    output_path = tmp_path / "output.jsonl"
    with unittest.mock.patch("sys.argv", ["export_jsonl.py", str(input_path), str(output_path)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL" in captured.err

import json
import pytest
from pathlib import Path
from unittest.mock import patch
import sys
from tools.export_jsonl import export_jsonl, main


def test_export_jsonl_success(tmp_path):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"
    data = {
        "document_id": "doc123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"article_id": "art1", "headline": "Headline 1"},
                    {"article_id": "art2", "headline": "Headline 2"}
                ]
            }
        ]
    }
    input_json.write_text(json.dumps(data), encoding="utf-8")
    export_jsonl(input_json, output_jsonl)
    assert output_jsonl.exists()
    lines = output_jsonl.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    parsed1 = json.loads(lines[0])
    assert parsed1["document_id"] == "doc123"
    assert parsed1["page_number"] == 1
    assert parsed1["article_id"] == "art1"


def test_export_jsonl_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        export_jsonl(tmp_path / "missing.json", tmp_path / "out.jsonl")


def test_export_jsonl_invalid_suffix(tmp_path):
    p = tmp_path / "test.txt"
    p.touch()
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        export_jsonl(p, tmp_path / "out.jsonl")


def test_export_jsonl_invalid_json(tmp_path):
    p = tmp_path / "test.json"
    p.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(p, tmp_path / "out.jsonl")


def test_export_jsonl_non_finite(tmp_path):
    p = tmp_path / "test.json"
    p.write_text("{\"pages\": NaN}", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(p, tmp_path / "out.jsonl")


def test_export_jsonl_not_dict(tmp_path):
    p = tmp_path / "test.json"
    p.write_text("[]", encoding="utf-8")
    export_jsonl(p, tmp_path / "out.jsonl")
    assert not (tmp_path / "out.jsonl").exists()


def test_export_jsonl_pages_not_list(tmp_path):
    p = tmp_path / "test.json"
    p.write_text("{\"pages\": {}}", encoding="utf-8")
    export_jsonl(p, tmp_path / "out.jsonl")
    assert not (tmp_path / "out.jsonl").exists()


def test_export_jsonl_page_not_dict(tmp_path):
    p = tmp_path / "test.json"
    p.write_text("{\"pages\": [1]}", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    export_jsonl(p, out)
    assert out.exists()
    assert out.read_text(encoding="utf-8") == ""


def test_export_jsonl_articles_not_list(tmp_path):
    p = tmp_path / "test.json"
    p.write_text("{\"pages\": [{\"articles\": {}}]}", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    export_jsonl(p, out)
    assert out.exists()
    assert out.read_text(encoding="utf-8") == ""


def test_export_jsonl_article_not_dict(tmp_path):
    p = tmp_path / "test.json"
    p.write_text("{\"pages\": [{\"articles\": [1]}]}", encoding="utf-8")
    out = tmp_path / "out.jsonl"
    export_jsonl(p, out)
    assert out.exists()
    assert out.read_text(encoding="utf-8") == ""


def test_main_success(tmp_path, capsys):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"
    input_json.write_text("{\"pages\": []}", encoding="utf-8")
    with patch("sys.argv", ["export_jsonl.py", str(input_json), str(output_jsonl)]):
        main()
    captured = capsys.readouterr()
    assert "successfully written" in captured.out


def test_main_exception(tmp_path, capsys):
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"
    input_json.write_text("{\"pages\": []}", encoding="utf-8")
    with patch("sys.argv", ["export_jsonl.py", str(input_json), str(output_jsonl)]):
        with patch("tools.export_jsonl.export_jsonl", side_effect=OSError("test err")):
            with pytest.raises(SystemExit) as exc:
                main()
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "test err" in captured.err

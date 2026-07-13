import json
import sys

import pytest

from tools.split_dom import main, split_dom


def test_split_dom_success(tmp_path):
    input_file = tmp_path / "input.json"
    output_dir = tmp_path / "out"

    data = {
        "document_id": "test_doc",
        "pages": [
            {"page_number": 1, "articles": [{"article_id": "a1", "headline": "H1"}]},
            {"page_number": 2, "articles": [{"article_id": "a2", "headline": "H2"}]},
        ],
        "quality": {"status": "success", "parser": "mineru"},
    }
    input_file.write_text(json.dumps(data))

    split_dom(input_file, output_dir)

    assert (output_dir / "input_page_1.json").exists()
    assert (output_dir / "input_page_2.json").exists()

    p1 = json.loads((output_dir / "input_page_1.json").read_text())
    assert p1["document_id"] == "test_doc_page_1"
    assert len(p1["pages"]) == 1
    assert p1["pages"][0]["page_number"] == 1

    p2 = json.loads((output_dir / "input_page_2.json").read_text())
    assert p2["document_id"] == "test_doc_page_2"
    assert len(p2["pages"]) == 1
    assert p2["pages"][0]["page_number"] == 2


def test_split_dom_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="File not found"):
        split_dom(tmp_path / "nonexistent.json", tmp_path / "out")


def test_split_dom_invalid_extension(tmp_path):
    input_file = tmp_path / "input.txt"
    input_file.touch()
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        split_dom(input_file, tmp_path / "out")


def test_split_dom_invalid_json(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text("not json")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        split_dom(input_file, tmp_path / "out")


def test_split_dom_schema_validation_error(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps({"invalid": "data"}))
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        split_dom(input_file, tmp_path / "out")


def test_split_dom_no_pages(tmp_path):
    input_file = tmp_path / "input.json"
    data = {
        "document_id": "test_doc",
        "pages": [],
        "quality": {"status": "success", "parser": "mineru"},
    }
    input_file.write_text(json.dumps(data))
    output_dir = tmp_path / "out"
    split_dom(input_file, output_dir)

    assert output_dir.exists()
    assert len(list(output_dir.iterdir())) == 0


def test_main_success(tmp_path, monkeypatch, capsys):
    input_file = tmp_path / "input.json"
    output_dir = tmp_path / "out"
    data = {
        "document_id": "test_doc",
        "pages": [
            {"page_number": 1, "articles": [{"article_id": "a1", "headline": "H1"}]}
        ],
        "quality": {"status": "success"},
    }
    input_file.write_text(json.dumps(data))

    main([str(input_file), "-o", str(output_dir)])
    captured = capsys.readouterr()
    assert "DOM splitting completed successfully." in captured.out


def test_main_error(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([str(tmp_path / "nonexistent.json"), "-o", str(tmp_path / "out")])
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error splitting JSON file: File not found" in captured.err


def test_sys_path_injection_split(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "path", [])
    import runpy

    runpy.run_path("tools/split_dom.py")

from pathlib import Path
import json
import sys

import pytest

from tools.filter_dom import main, filter_dom


def test_filter_dom_success(tmp_path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "out.json"

    data = {
        "document_id": "test_doc",
        "pages": [
            {"page_number": 1, "articles": [{"article_id": "a1", "headline": "H1"}]},
            {"page_number": 2, "articles": [{"article_id": "a2", "headline": "H2"}]},
            {"page_number": 3, "articles": [{"article_id": "a3", "headline": "H3"}]},
        ],
        "quality": {"status": "success", "parser": "mineru"},
    }
    input_file.write_text(json.dumps(data))

    filter_dom(input_file, output_file, pages=[1, 3])

    assert output_file.exists()
    out_data = json.loads(output_file.read_text())
    assert len(out_data["pages"]) == 2
    assert out_data["pages"][0]["page_number"] == 1
    assert out_data["pages"][1]["page_number"] == 3


def test_filter_dom_no_pages_arg(tmp_path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "out.json"

    data = {
        "document_id": "test_doc",
        "pages": [
            {"page_number": 1, "articles": [{"article_id": "a1", "headline": "H1"}]},
        ],
        "quality": {"status": "success", "parser": "mineru"},
    }
    input_file.write_text(json.dumps(data))

    filter_dom(input_file, output_file)

    assert output_file.exists()
    out_data = json.loads(output_file.read_text())
    assert len(out_data["pages"]) == 1


def test_filter_dom_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="File not found"):
        filter_dom(tmp_path / "nonexistent.json", tmp_path / "out.json")


def test_filter_dom_invalid_extension(tmp_path):
    input_file = tmp_path / "input.txt"
    input_file.touch()
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        filter_dom(input_file, tmp_path / "out.json")


def test_filter_dom_invalid_json(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text("not json")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(input_file, tmp_path / "out.json")


def test_filter_dom_schema_validation_error(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps({"invalid": "data"}))
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        filter_dom(input_file, tmp_path / "out.json")


def test_main_success(tmp_path, monkeypatch, capsys):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "out.json"
    data = {
        "document_id": "test_doc",
        "pages": [
            {"page_number": 1, "articles": [{"article_id": "a1", "headline": "H1"}]},
            {"page_number": 2, "articles": [{"article_id": "a2", "headline": "H2"}]},
        ],
        "quality": {"status": "success"},
    }
    input_file.write_text(json.dumps(data))

    main([str(input_file), "-o", str(output_file), "-p", "1"])
    captured = capsys.readouterr()
    assert "Filtered JSON successfully written to" in captured.out


def test_main_invalid_pages(tmp_path, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([str(tmp_path / "input.json"), "-o", str(tmp_path / "out.json"), "-p", "1,a,3"])
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error: --pages must be a comma-separated list of integers." in captured.err


def test_main_error(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([str(tmp_path / "nonexistent.json"), "-o", str(tmp_path / "out.json")])
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error filtering JSON file: File not found" in captured.err


def test_sys_path_injection_filter(tmp_path, monkeypatch):
    import sys
    from pathlib import Path
    import importlib
    import tools.filter_dom

    src_path = str(Path(__file__).resolve().parents[1] / "src")
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != src_path])

    importlib.reload(tools.filter_dom)
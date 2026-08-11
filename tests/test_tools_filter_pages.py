import json
import runpy
import sys
from pathlib import Path
import pytest
from tools.filter_pages import filter_pages, main

def test_filter_pages(tmp_path: Path):
    json_file = tmp_path / "test.json"
    data = {"pages": [{"page_number": 1}, {"page_number": 2}, {"page_number": 3}]}
    json_file.write_text(json.dumps(data), encoding="utf-8")
    result = filter_pages(json_file, 2, 3)
    assert len(result["pages"]) == 2
    assert result["pages"][0]["page_number"] == 2
    assert result["pages"][1]["page_number"] == 3

def test_filter_pages_file_not_found(tmp_path: Path):
    json_file = tmp_path / "nonexistent.json"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        filter_pages(json_file, 1, 2)

def test_filter_pages_invalid_extension(tmp_path: Path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match=r"File must be a \.json file\."):
        filter_pages(txt_file, 1, 2)

def test_filter_pages_reversed_range(tmp_path: Path):
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps({"pages": []}), encoding="utf-8")
    with pytest.raises(ValueError, match=r"start_page must not exceed end_page\."):
        filter_pages(json_file, 3, 2)

def test_main_success(tmp_path: Path, capsys, monkeypatch):
    json_file = tmp_path / "test.json"
    data = {"pages": [{"page_number": 1}, {"page_number": 2}]}
    json_file.write_text(json.dumps(data), encoding="utf-8")
    main([str(json_file), "--start-page", "2", "--end-page", "2"])
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert len(output["pages"]) == 1
    assert output["pages"][0]["page_number"] == 2

def test_main_error(tmp_path: Path, capsys, monkeypatch):
    json_file = tmp_path / "nonexistent.json"
    with pytest.raises(SystemExit) as exc_info:
        main([str(json_file), "--start-page", "1", "--end-page", "2"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: File not found or is not a file:" in captured.err

def test_module_entrypoint(tmp_path: Path, capsys, monkeypatch):
    json_file = tmp_path / "test.json"
    json_file.write_text(
        json.dumps({"pages": [{"page_number": 1}]}), encoding="utf-8"
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["filter_pages", str(json_file), "--start-page", "1", "--end-page", "1"],
    )
    runpy.run_path(
        str(Path(__file__).parents[1] / "tools" / "filter_pages.py"),
        run_name="__main__",
    )
    assert json.loads(capsys.readouterr().out)["pages"][0]["page_number"] == 1

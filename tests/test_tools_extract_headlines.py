import json
import sys
from pathlib import Path
import pytest
from tools.extract_headlines import extract_headlines, main

def test_extract_headlines(tmp_path: Path):
    json_file = tmp_path / "test.json"
    data = {"pages": [{"articles": [{"headline": "Test 1"}, {"headline": "Test 2"}]}]}
    json_file.write_text(json.dumps(data), encoding="utf-8")
    result = extract_headlines(json_file)
    assert result == ["Test 1", "Test 2"]

def test_extract_headlines_file_not_found(tmp_path: Path):
    json_file = tmp_path / "nonexistent.json"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        extract_headlines(json_file)

def test_extract_headlines_invalid_extension(tmp_path: Path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="File must be a .json file."):
        extract_headlines(txt_file)

def test_main_success_stdout(tmp_path: Path, capsys, monkeypatch):
    json_file = tmp_path / "test.json"
    data = {"pages": [{"articles": [{"headline": "Test 1"}]}]}
    json_file.write_text(json.dumps(data), encoding="utf-8")
    main([str(json_file)])
    captured = capsys.readouterr()
    assert "Test 1\n" in captured.out

def test_main_success_file(tmp_path: Path, capsys, monkeypatch):
    json_file = tmp_path / "test.json"
    out_file = tmp_path / "out.txt"
    data = {"pages": [{"articles": [{"headline": "Test 1"}]}]}
    json_file.write_text(json.dumps(data), encoding="utf-8")
    main([str(json_file), "--output", str(out_file)])
    captured = capsys.readouterr()
    assert "Extracted 1 headlines to" in captured.out
    assert out_file.read_text(encoding="utf-8") == "Test 1\n"

def test_main_error(tmp_path: Path, capsys, monkeypatch):
    json_file = tmp_path / "nonexistent.json"
    with pytest.raises(SystemExit) as exc_info:
        main([str(json_file)])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: File not found or is not a file:" in captured.err

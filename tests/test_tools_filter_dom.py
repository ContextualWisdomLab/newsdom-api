from __future__ import annotations
import runpy
import sys

import json
from pathlib import Path
import pytest

from tools.filter_dom import main, filter_dom

@pytest.fixture
def valid_dom_data():
    return {
        "document_id": "test-doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"article_id": "art-1", "headline": "Headline 1", "body_blocks": [], "images": [], "captions": [], "footnotes": []},
                    {"article_id": "art-2", "headline": "Headline 2", "body_blocks": [], "images": [], "captions": [], "footnotes": []}
                ],
                "ads": [], "headers": [], "footers": [], "page_numbers": []
            },
            {
                "page_number": 2,
                "articles": [
                    {"article_id": "art-3", "headline": "Headline 3", "body_blocks": [], "images": [], "captions": [], "footnotes": []}
                ],
                "ads": [], "headers": [], "footers": [], "page_numbers": []
            }
        ],
        "quality": {"status": "success", "parser": "mineru", "warnings": []}
    }

def test_filter_dom_no_filters(tmp_path: Path, valid_dom_data: dict) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(valid_dom_data), encoding="utf-8")

    result = filter_dom(input_file)
    assert len(result["pages"]) == 2
    assert len(result["pages"][0]["articles"]) == 2

def test_filter_dom_by_pages(tmp_path: Path, valid_dom_data: dict) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(valid_dom_data), encoding="utf-8")

    result = filter_dom(input_file, pages_to_keep=[2])
    assert len(result["pages"]) == 1
    assert result["pages"][0]["page_number"] == 2
    assert len(result["pages"][0]["articles"]) == 1

def test_filter_dom_by_articles(tmp_path: Path, valid_dom_data: dict) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(valid_dom_data), encoding="utf-8")

    result = filter_dom(input_file, articles_to_keep=["art-1", "art-3"])
    assert len(result["pages"]) == 2
    assert len(result["pages"][0]["articles"]) == 1
    assert result["pages"][0]["articles"][0]["article_id"] == "art-1"
    assert len(result["pages"][1]["articles"]) == 1
    assert result["pages"][1]["articles"][0]["article_id"] == "art-3"

def test_filter_dom_file_not_found(tmp_path: Path) -> None:
    non_existent = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        filter_dom(non_existent)

def test_filter_dom_invalid_extension(tmp_path: Path) -> None:
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        filter_dom(txt_path)

def test_filter_dom_invalid_json(tmp_path: Path) -> None:
    json_path = tmp_path / "invalid_json.json"
    json_path.write_text("invalid{json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(json_path)

def test_filter_dom_validation_error(tmp_path: Path) -> None:
    json_path = tmp_path / "invalid_schema.json"
    invalid_data = {"pages": []}
    json_path.write_text(json.dumps(invalid_data), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        filter_dom(json_path)

def test_main_with_output_file(tmp_path: Path, valid_dom_data: dict, capsys: pytest.CaptureFixture[str]) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(valid_dom_data), encoding="utf-8")

    output_file = tmp_path / "output.json"

    main([str(input_file), "-o", str(output_file), "--pages", "1"])

    captured = capsys.readouterr()
    assert "Filtered DOM successfully written to" in captured.out

    out_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(out_data["pages"]) == 1

def test_main_stdout(tmp_path: Path, valid_dom_data: dict, capsys: pytest.CaptureFixture[str]) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(valid_dom_data), encoding="utf-8")

    main([str(input_file), "--articles", "art-2"])

    captured = capsys.readouterr()
    out_data = json.loads(captured.out)
    assert len(out_data["pages"]) == 2
    assert len(out_data["pages"][0]["articles"]) == 1
    assert out_data["pages"][0]["articles"][0]["article_id"] == "art-2"

def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    non_existent = tmp_path / "missing.json"

    with pytest.raises(SystemExit) as exc_info:
        main([str(non_existent)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error filtering JSON file:" in captured.err

def test_sys_path_injection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_dom_data: dict) -> None:
    monkeypatch.setattr(sys, "path", [])

    json_path = tmp_path / "valid.json"
    json_path.write_text(json.dumps(valid_dom_data), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["filter_dom.py", str(json_path)])

    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        runpy.run_module("tools.filter_dom", run_name="__main__")

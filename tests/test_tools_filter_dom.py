import importlib
import json
import sys
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

import tools.filter_dom
from tools.filter_dom import filter_dom, main


@pytest.fixture
def sample_json(tmp_path: Path) -> Path:
    data = {
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"headline": "Test One", "body_blocks": ["Hello world"]},
                    {"headline": "Another", "body_blocks": ["foo bar"]}
                ]
            },
            {
                "page_number": 2,
                "articles": [
                    {"headline": "Test Two", "body_blocks": ["world peace"]}
                ]
            }
        ]
    }
    file_path = tmp_path / "sample.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


def test_filter_dom_by_query(sample_json: Path, tmp_path: Path):
    out = tmp_path / "out.json"
    filter_dom(sample_json, out, query="world")
    res = json.loads(out.read_text())
    assert len(res["pages"]) == 2
    assert len(res["pages"][0]["articles"]) == 1
    assert res["pages"][0]["articles"][0]["headline"] == "Test One"


def test_filter_dom_by_page(sample_json: Path, tmp_path: Path):
    out = tmp_path / "out.json"
    filter_dom(sample_json, out, page_num=2)
    res = json.loads(out.read_text())
    assert len(res["pages"]) == 1
    assert res["pages"][0]["page_number"] == 2


def test_filter_dom_by_query_and_page(sample_json: Path, tmp_path: Path):
    out = tmp_path / "out.json"
    filter_dom(sample_json, out, query="foo", page_num=1)
    res = json.loads(out.read_text())
    assert len(res["pages"]) == 1
    assert len(res["pages"][0]["articles"]) == 1
    assert res["pages"][0]["articles"][0]["headline"] == "Another"


def test_filter_dom_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="File not found"):
        filter_dom(tmp_path / "nonexistent.json", tmp_path / "out.json")


def test_filter_dom_invalid_input_suffix(tmp_path: Path):
    invalid = tmp_path / "test.txt"
    invalid.touch()
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        filter_dom(invalid, tmp_path / "out.json")


def test_filter_dom_invalid_output_suffix(sample_json: Path, tmp_path: Path):
    with pytest.raises(ValueError, match="Output file must be a .json file"):
        filter_dom(sample_json, tmp_path / "out.txt")


def test_filter_dom_invalid_json(tmp_path: Path):
    invalid = tmp_path / "bad.json"
    invalid.write_text("invalid json")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(invalid, tmp_path / "out.json")


def test_main_success(sample_json: Path, tmp_path: Path, capsys: pytest.CaptureFixture):
    out = tmp_path / "out.json"
    main([str(sample_json), str(out), "-q", "Test"])
    cap = capsys.readouterr()
    assert "Filtered DOM saved to" in cap.out


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture):
    with pytest.raises(SystemExit):
        main([str(tmp_path / "non.json"), str(tmp_path / "out.json")])
    cap = capsys.readouterr()
    assert "Error:" in cap.err


def test_module_execution(monkeypatch: MonkeyPatch):
    monkeypatch.setattr(sys, "argv", ["filter_dom.py", "-h"])
    with pytest.raises(SystemExit):
        importlib.reload(tools.filter_dom)
        tools.filter_dom.main()

def test_filter_dom_by_page_no_articles(tmp_path: Path):
    data = {
        "pages": [
            {
                "page_number": 3,
                "articles": []
            }
        ]
    }
    file_path = tmp_path / "sample2.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    out = tmp_path / "out2.json"
    filter_dom(file_path, out, page_num=3)
    res = json.loads(out.read_text())
    assert len(res["pages"]) == 1
    assert len(res["pages"][0]["articles"]) == 0

def test_filter_dom_no_match(sample_json: Path, tmp_path: Path):
    out = tmp_path / "out3.json"
    filter_dom(sample_json, out, query="nomatch")
    res = json.loads(out.read_text())
    assert len(res["pages"]) == 0

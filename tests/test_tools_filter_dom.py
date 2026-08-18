from __future__ import annotations

import json
from pathlib import Path

import pytest
import importlib
import sys

from tools import filter_dom


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample.json"
    data = {
        "pages": [
            {
                "articles": [
                    {"body_blocks": ["text1"]},
                    {"body_blocks": ["text1", "text2"]},
                ]
            }
        ]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path

@pytest.fixture
def empty_page_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "empty_page.json"
    data = {
        "pages": [
            {"articles": []}
        ]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_filter_dom_stdout(mock_json_file, capsys):
    filter_dom.main([str(mock_json_file), "--min-blocks", "2"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data["pages"][0]["articles"]) == 1
    assert len(data["pages"][0]["articles"][0]["body_blocks"]) == 2


def test_filter_dom_output_file(mock_json_file, tmp_path):
    output_path = tmp_path / "output.json"
    filter_dom.main([str(mock_json_file), "--min-blocks", "2", "-o", str(output_path)])
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(data["pages"][0]["articles"]) == 1
    assert len(data["pages"][0]["articles"][0]["body_blocks"]) == 2


def test_filter_dom_empty_articles(empty_page_json_file, capsys):
    filter_dom.main([str(empty_page_json_file), "--min-blocks", "1"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data["pages"][0]["articles"]) == 0

def test_filter_dom_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(tmp_path / "missing.json"), "--min-blocks", "1"])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err


def test_filter_dom_wrong_ext(tmp_path, capsys):
    txt = tmp_path / "wrong.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(txt), "--min-blocks", "1"])
    assert e.value.code == 1
    assert "must be a .json file" in capsys.readouterr().err


def test_filter_dom_invalid_json(tmp_path, capsys):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{bad json", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(bad_json), "--min-blocks", "1"])
    assert e.value.code == 1
    assert "Invalid JSON file" in capsys.readouterr().err

def test_filter_dom_main_branch(monkeypatch):
    """Test the if __name__ == '__main__': block for 100% coverage."""
    monkeypatch.setattr(sys, "argv", ["filter_dom.py", "-h"])
    with pytest.raises(SystemExit) as e:
        import runpy
        runpy.run_module("tools.filter_dom", run_name="__main__")

    assert e.value.code == 0
def test_filter_dom_articles_not_filtered_but_present(tmp_path, capsys):
    json_path = tmp_path / "sample.json"
    data = {
        "pages": [
            {
                "articles": [
                    {"body_blocks": []}
                ]
            }
        ]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")

    filter_dom.main([str(json_path), "--min-blocks", "1"])
    out = capsys.readouterr().out
    data_out = json.loads(out)
    assert len(data_out["pages"]) == 0

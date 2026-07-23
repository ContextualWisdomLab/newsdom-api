from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import compare_dom


@pytest.fixture
def mock_json_file1(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample1.json"
    data = {
        "pages": [{"articles": [{"body_blocks": ["text1", "text2"], "images": [{}]}]}]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


@pytest.fixture
def mock_json_file2(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample2.json"
    data = {"pages": [{"articles": [{"body_blocks": ["text1"], "images": []}]}]}
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_compare_dom_success(mock_json_file1, mock_json_file2, capsys):
    compare_dom.main([str(mock_json_file1), str(mock_json_file2)])
    out = capsys.readouterr().out
    assert "num_pages: 1 -> 1 (Diff: 0)" in out
    assert "num_articles: 1 -> 1 (Diff: 0)" in out
    assert "num_body_blocks: 2 -> 1 (Diff: -1)" in out
    assert "num_images: 1 -> 0 (Diff: -1)" in out


def test_compare_dom_not_found(tmp_path, mock_json_file1, capsys):
    with pytest.raises(SystemExit) as e:
        compare_dom.main([str(mock_json_file1), str(tmp_path / "missing.json")])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err

    with pytest.raises(SystemExit) as e:
        compare_dom.main([str(tmp_path / "missing.json"), str(mock_json_file1)])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err


def test_compare_dom_wrong_ext(tmp_path, mock_json_file1, capsys):
    txt = tmp_path / "wrong.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        compare_dom.main([str(mock_json_file1), str(txt)])
    assert e.value.code == 1
    assert "must be .json files" in capsys.readouterr().err

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import analyze_dom


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample.json"
    data = {
        "pages": [{"articles": [{"body_blocks": ["text1", "text2"], "images": [{}]}]}]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_analyze_dom_success(mock_json_file, capsys):
    analyze_dom.main([str(mock_json_file)])
    out = capsys.readouterr().out
    assert "Pages: 1" in out
    assert "Articles: 1" in out
    assert "Body Blocks: 2" in out
    assert "Images: 1" in out


def test_analyze_dom_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        analyze_dom.main([str(tmp_path / "missing.json")])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err


def test_analyze_dom_wrong_ext(tmp_path, capsys):
    txt = tmp_path / "wrong.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        analyze_dom.main([str(txt)])
    assert e.value.code == 1
    assert "must be a .json file" in capsys.readouterr().err

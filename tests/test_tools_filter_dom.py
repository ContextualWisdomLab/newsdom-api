from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import filter_dom


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample.json"
    data = {
        "pages": [
            {"articles": [{"body_blocks": ["text1"]}]},
            {"articles": []},
            {"articles": [{"body_blocks": ["text2"]}, {"body_blocks": ["text3"]}]},
        ]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_filter_dom_success(tmp_path, mock_json_file, capsys):
    out_path = tmp_path / "out.json"
    filter_dom.main([str(mock_json_file), str(out_path), "--min-articles", "1"])

    out = capsys.readouterr().out
    assert "Successfully filtered" in out

    data = json.loads(out_path.read_bytes())
    assert len(data["pages"]) == 2


def test_filter_dom_not_found(tmp_path, capsys):
    out_path = tmp_path / "out.json"
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(tmp_path / "missing.json"), str(out_path)])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err


def test_filter_dom_wrong_ext_in(tmp_path, capsys):
    txt = tmp_path / "wrong.txt"
    txt.write_text("test", encoding="utf-8")
    out_path = tmp_path / "out.json"
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(txt), str(out_path)])
    assert e.value.code == 1
    assert "Input must be a .json file" in capsys.readouterr().err


def test_filter_dom_wrong_ext_out(tmp_path, mock_json_file, capsys):
    out_path = tmp_path / "out.txt"
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(mock_json_file), str(out_path)])
    assert e.value.code == 1
    assert "Output must be a .json file" in capsys.readouterr().err

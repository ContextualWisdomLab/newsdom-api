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
            {
                "articles": [
                    {"headline": "Apple is a fruit", "body_blocks": ["Delicious."]},
                    {"headline": "Banana", "body_blocks": ["Also delicious.", "Yellow."]}
                ]
            }
        ]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_filter_dom_success_stdout(mock_json_file, capsys):
    filter_dom.main([str(mock_json_file), "Apple"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data["pages"]) == 1
    assert len(data["pages"][0]["articles"]) == 1
    assert data["pages"][0]["articles"][0]["headline"] == "Apple is a fruit"


def test_filter_dom_success_output_file(mock_json_file, tmp_path):
    output_path = tmp_path / "output.json"
    filter_dom.main([str(mock_json_file), "Yellow", "-o", str(output_path)])
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(data["pages"]) == 1
    assert len(data["pages"][0]["articles"]) == 1
    assert data["pages"][0]["articles"][0]["headline"] == "Banana"


def test_filter_dom_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(tmp_path / "missing.json"), "test"])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err


def test_filter_dom_wrong_ext(tmp_path, capsys):
    txt = tmp_path / "wrong.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(txt), "test"])
    assert e.value.code == 1
    assert "must be a .json file" in capsys.readouterr().err

def test_filter_dom_no_match(mock_json_file, capsys):
    filter_dom.main([str(mock_json_file), "Cherry"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data["pages"]) == 0

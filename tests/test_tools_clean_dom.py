from __future__ import annotations

import json
from pathlib import Path

import pytest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import clean_dom


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample.json"
    data = {
        "pages": [
            {
                "articles": [{"headline": "Test"}],
                "ads": ["Ad 1", "Ad 2"],
                "headers": ["Header 1"],
                "footers": ["Footer 1"],
            },
            {"articles": [{"headline": "Test 2"}], "page_number": 2},
        ]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_clean_dom_success(mock_json_file, tmp_path, capsys):
    output_file = tmp_path / "output.json"
    clean_dom.main([str(mock_json_file), str(output_file)])
    out = capsys.readouterr().out
    assert "Successfully cleaned DOM" in out

    data = json.loads(output_file.read_text(encoding="utf-8"))
    page1 = data["pages"][0]
    assert page1["ads"] == []
    assert page1["headers"] == []
    assert page1["footers"] == []
    assert len(page1["articles"]) == 1

    page2 = data["pages"][1]
    assert "ads" not in page2
    assert "headers" not in page2
    assert "footers" not in page2


def test_clean_dom_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        clean_dom.main([str(tmp_path / "missing.json"), str(tmp_path / "out.json")])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err


def test_clean_dom_wrong_input_ext(tmp_path, capsys):
    txt = tmp_path / "wrong.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        clean_dom.main([str(txt), str(tmp_path / "out.json")])
    assert e.value.code == 1
    assert "Input must be a .json file" in capsys.readouterr().err


def test_clean_dom_wrong_output_ext(mock_json_file, tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        clean_dom.main([str(mock_json_file), str(tmp_path / "out.txt")])
    assert e.value.code == 1
    assert "Output must be a .json file" in capsys.readouterr().err

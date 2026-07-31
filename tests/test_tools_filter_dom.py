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
                "ads": ["ad1", "ad2"],
                "headers": ["header1"],
                "footers": ["footer1"],
                "page_numbers": ["1"],
                "articles": [{"images": [{"path": "img1.png"}, {"path": "img2.png"}]}],
            }
        ]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_filter_dom_no_pages(tmp_path):
    json_path = tmp_path / "no_pages.json"
    json_path.write_text(json.dumps({"other": "data"}), encoding="utf-8")
    out_path = tmp_path / "out.json"
    filter_dom.main([str(json_path), str(out_path), "--exclude-ads"])

    out_data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "pages" not in out_data
    assert out_data["other"] == "data"


def test_filter_dom_success(mock_json_file, tmp_path):
    out_path = tmp_path / "out.json"
    filter_dom.main(
        [
            str(mock_json_file),
            str(out_path),
            "--exclude-ads",
            "--exclude-headers",
            "--exclude-footers",
            "--exclude-page-numbers",
            "--exclude-images",
        ]
    )

    out_data = json.loads(out_path.read_text(encoding="utf-8"))
    page = out_data["pages"][0]
    assert page["ads"] == []
    assert page["headers"] == []
    assert page["footers"] == []
    assert page["page_numbers"] == []
    assert page["articles"][0]["images"] == []


def test_filter_dom_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(tmp_path / "missing.json"), str(tmp_path / "out.json")])
    assert e.value.code == 1
    assert "not found" in capsys.readouterr().err


def test_filter_dom_invalid_json(tmp_path, capsys):
    txt = tmp_path / "invalid.json"
    txt.write_text("invalid json", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(txt), str(tmp_path / "out.json")])
    assert e.value.code == 1
    assert "Error decoding JSON" in capsys.readouterr().err

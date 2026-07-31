from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import shift_bboxes


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample.json"
    data = {
        "pages": [
            {
                "articles": [
                    {
                        "bbox": {"x0": 10, "y0": 20, "x1": 30, "y1": 40},
                        "images": [
                            {
                                "bbox": {"x0": 5},
                                "captions": [{"bbox": {"x1": 50}}],
                                "footnotes": [{"bbox": {"y0": 10}}],
                            }
                        ],
                        "captions": [{"bbox": {"y1": 100}}],
                        "footnotes": [{"bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}}],
                    }
                ]
            }
        ]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_shift_bboxes_no_pages(tmp_path):
    json_path = tmp_path / "no_pages.json"
    json_path.write_text(json.dumps({"other": "data"}), encoding="utf-8")
    out_path = tmp_path / "out.json"
    shift_bboxes.main([str(json_path), str(out_path), "--dx", "10", "--dy", "20"])

    out_data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "pages" not in out_data
    assert out_data["other"] == "data"


def test_shift_bboxes_success(mock_json_file, tmp_path):
    out_path = tmp_path / "out.json"
    shift_bboxes.main(
        [str(mock_json_file), str(out_path), "--dx", "100.0", "--dy", "200.0"]
    )

    out_data = json.loads(out_path.read_text(encoding="utf-8"))
    article = out_data["pages"][0]["articles"][0]

    assert article["bbox"] == {"x0": 110, "y0": 220, "x1": 130, "y1": 240}
    assert article["images"][0]["bbox"] == {"x0": 105}
    assert article["images"][0]["captions"][0]["bbox"] == {"x1": 150}
    assert article["images"][0]["footnotes"][0]["bbox"] == {"y0": 210}
    assert article["captions"][0]["bbox"] == {"y1": 300}
    assert article["footnotes"][0]["bbox"] == {
        "x0": 100,
        "y0": 200,
        "x1": 100,
        "y1": 200,
    }


def test_shift_bboxes_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        shift_bboxes.main([str(tmp_path / "missing.json"), str(tmp_path / "out.json")])
    assert e.value.code == 1
    assert "not found" in capsys.readouterr().err


def test_shift_bboxes_invalid_json(tmp_path, capsys):
    txt = tmp_path / "invalid.json"
    txt.write_text("invalid json", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        shift_bboxes.main([str(txt), str(tmp_path / "out.json")])
    assert e.value.code == 1
    assert "Error decoding JSON" in capsys.readouterr().err

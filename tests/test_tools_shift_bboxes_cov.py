from __future__ import annotations

import json

from tools import shift_bboxes


def test_shift_bboxes_branches(tmp_path):
    # Test skipping empty or missing bboxes
    data = {
        "pages": [
            {
                "articles": [
                    {
                        "bbox": None,
                        "images": [
                            {
                                "bbox": {},
                                "captions": [{"bbox": None}],
                                "footnotes": [{"bbox": {}}],
                            }
                        ],
                        "captions": [{"bbox": None}],
                        "footnotes": [{"bbox": {}}],
                    }
                ]
            }
        ]
    }
    json_path = tmp_path / "sample.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    out_path = tmp_path / "out.json"

    shift_bboxes.main([str(json_path), str(out_path), "--dx", "10", "--dy", "20"])

    out_data = json.loads(out_path.read_text(encoding="utf-8"))
    article = out_data["pages"][0]["articles"][0]

    assert article["bbox"] is None
    assert article["images"][0]["bbox"] == {}
    assert article["images"][0]["captions"][0]["bbox"] is None
    assert article["images"][0]["footnotes"][0]["bbox"] == {}
    assert article["captions"][0]["bbox"] is None
    assert article["footnotes"][0]["bbox"] == {}

    # Test shifting missing fields
    data2 = {
        "pages": [
            {
                "articles": [
                    {
                        "bbox": {"x0": 10},  # Missing x1, y0, y1
                        "images": [],
                        "captions": [],
                        "footnotes": [],
                    }
                ]
            }
        ]
    }
    json_path2 = tmp_path / "sample2.json"
    json_path2.write_text(json.dumps(data2), encoding="utf-8")
    out_path2 = tmp_path / "out2.json"
    shift_bboxes.main([str(json_path2), str(out_path2), "--dx", "10", "--dy", "20"])

    out_data2 = json.loads(out_path2.read_text(encoding="utf-8"))
    article2 = out_data2["pages"][0]["articles"][0]
    assert article2["bbox"] == {"x0": 20}

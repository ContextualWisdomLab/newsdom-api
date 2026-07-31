from __future__ import annotations

import json

from tools import filter_dom


def test_filter_dom_branches(tmp_path):
    data = {
        "pages": [
            {
                "ads": ["ad1"],
                "headers": ["h1"],
                "footers": ["f1"],
                "page_numbers": ["p1"],
                "articles": [{"images": [{"path": "img1"}]}],
            }
        ]
    }
    json_path = tmp_path / "sample.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    out_path = tmp_path / "out.json"

    # Test with no exclusions
    filter_dom.main([str(json_path), str(out_path)])
    out_data = json.loads(out_path.read_text(encoding="utf-8"))
    page = out_data["pages"][0]
    assert page["ads"] == ["ad1"]
    assert page["headers"] == ["h1"]
    assert page["footers"] == ["f1"]
    assert page["page_numbers"] == ["p1"]
    assert page["articles"][0]["images"] == [{"path": "img1"}]

    # Test with partial missing fields to hit the other branch
    data2 = {
        "pages": [
            {
                # Missing ads, headers, footers, page_numbers, images
                "articles": [{}]
            }
        ]
    }
    json_path2 = tmp_path / "sample2.json"
    json_path2.write_text(json.dumps(data2), encoding="utf-8")
    out_path2 = tmp_path / "out2.json"

    filter_dom.main(
        [
            str(json_path2),
            str(out_path2),
            "--exclude-ads",
            "--exclude-headers",
            "--exclude-footers",
            "--exclude-page-numbers",
            "--exclude-images",
        ]
    )
    out_data2 = json.loads(out_path2.read_text(encoding="utf-8"))
    page2 = out_data2["pages"][0]
    assert "ads" not in page2
    assert "images" not in page2["articles"][0]

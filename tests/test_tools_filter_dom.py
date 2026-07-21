import json
import pytest
from tools.filter_dom import filter_dom, main


def test_filter_dom_invalid_file(tmp_path):
    not_exist = tmp_path / "not_exist.json"
    with pytest.raises(FileNotFoundError):
        filter_dom(not_exist)

    not_json = tmp_path / "test.txt"
    not_json.write_text("hello")
    with pytest.raises(ValueError, match="File must be a .json file."):
        filter_dom(not_json)

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{invalid: json}")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(invalid_json)


def test_filter_dom_logic(tmp_path):
    data = {
        "pages": [
            {
                "ads": ["ad1"],
                "headers": ["h1"],
                "footers": ["f1"],
                "articles": [
                    {
                        "images": [
                            {
                                "bbox": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
                                "captions": [{"bbox": {"x0": 0}}],
                                "footnotes": [{"bbox": {"x0": 0}}],
                            }
                        ],
                        "bbox": {"x0": 0},
                        "captions": [{"bbox": {"x0": 0}}],
                        "footnotes": [{"bbox": {"x0": 0}}],
                    }
                ],
            }
        ]
    }
    input_file = tmp_path / "test.json"
    input_file.write_text(json.dumps(data), encoding="utf-8")

    res = filter_dom(input_file, remove_ads=True)
    assert res["pages"][0]["ads"] == []
    assert res["pages"][0]["headers"] == ["h1"]

    res = filter_dom(input_file, remove_headers=True)
    assert res["pages"][0]["headers"] == []

    res = filter_dom(input_file, remove_footers=True)
    assert res["pages"][0]["footers"] == []

    res = filter_dom(input_file, remove_images=True)
    assert res["pages"][0]["articles"][0]["images"] == []

    res = filter_dom(input_file, remove_bboxes=True)
    art = res["pages"][0]["articles"][0]
    assert "bbox" not in art
    assert "bbox" not in art["images"][0]
    assert "bbox" not in art["images"][0]["captions"][0]
    assert "bbox" not in art["images"][0]["footnotes"][0]
    assert "bbox" not in art["captions"][0]
    assert "bbox" not in art["footnotes"][0]


def test_main_success(tmp_path, capsys):
    data = {"pages": [{"ads": ["ad"]}]}
    input_file = tmp_path / "test.json"
    input_file.write_text(json.dumps(data), encoding="utf-8")

    main([str(input_file), "--remove-ads"])
    captured = capsys.readouterr()
    assert '"ads": []' in captured.out

    out_file = tmp_path / "out.json"
    main([str(input_file), "-o", str(out_file), "--remove-ads"])
    out_data = json.loads(out_file.read_text())
    assert out_data["pages"][0]["ads"] == []


def test_main_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["invalid.json"])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_filter_dom_logic_no_captions_footnotes(tmp_path):
    data = {
        "pages": [
            {
                "articles": [
                    {
                        "images": [
                            {
                                "bbox": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
                            }
                        ],
                        "bbox": {"x0": 0},
                    }
                ],
            }
        ]
    }
    input_file = tmp_path / "test2.json"
    input_file.write_text(json.dumps(data), encoding="utf-8")

    res = filter_dom(input_file, remove_bboxes=True)
    art = res["pages"][0]["articles"][0]
    assert "bbox" not in art
    assert "bbox" not in art["images"][0]
def test_filter_dom_logic_full_misses(tmp_path):
    data = {
        "pages": [
            {
                "articles": [
                    {
                        "images": [
                            {
                                "captions": [{}],
                                "footnotes": [{}],
                            }
                        ],
                        "captions": [{}],
                        "footnotes": [{}],
                    }
                ],
            }
        ]
    }
    input_file = tmp_path / "test3.json"
    input_file.write_text(json.dumps(data), encoding="utf-8")

    res = filter_dom(input_file, remove_bboxes=True)
    art = res["pages"][0]["articles"][0]
    assert "bbox" not in art
def test_filter_dom_security_limits(tmp_path):
    # Depth limit
    deep_json = tmp_path / "deep.json"
    data = {}
    curr = data
    for _ in range(105):
        curr["a"] = {}
        curr = curr["a"]
    deep_json.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="nesting depth"):
        filter_dom(deep_json)

    # Depth list limit
    deep_list = tmp_path / "deeplist.json"
    data2 = []
    curr2 = data2
    for _ in range(105):
        curr2.append([])
        curr2 = curr2[0]
    deep_list.write_text(json.dumps(data2))
    with pytest.raises(ValueError, match="nesting depth"):
        filter_dom(deep_list)

    # File size limit
    big_file = tmp_path / "big.json"
    with big_file.open("wb") as f:
        f.seek(33 * 1024 * 1024)
        f.write(b"0")
    with pytest.raises(ValueError, match="32 MiB limit"):
        filter_dom(big_file)

def test_main_security_limits(tmp_path, capsys, monkeypatch):
    import os
    data = {"pages": [{"ads": ["ad"]}]}
    input_file = tmp_path / "test4.json"
    input_file.write_text(json.dumps(data), encoding="utf-8")

    # Symlink output
    out_file = tmp_path / "symlink.json"
    target = tmp_path / "target.json"
    target.write_text("{}")
    os.symlink(target, out_file)
    with pytest.raises(SystemExit):
        main([str(input_file), "-o", str(out_file)])

    # Output size limit
    def mock_dumps(*args, **kwargs):
        return "x" * (65 * 1024 * 1024)
    monkeypatch.setattr("json.dumps", mock_dumps)
    with pytest.raises(SystemExit):
        main([str(input_file)])

def test_filter_dom_schema_mismatch(tmp_path):
    data = {
        "pages": "notalist"
    }
    input_file = tmp_path / "schema.json"
    input_file.write_text(json.dumps(data), encoding="utf-8")
    res = filter_dom(input_file)
    assert res == data

    data2 = {
        "pages": [
            "notadict",
            {
                "articles": "notalist"
            },
            {
                "articles": [
                    "notadict",
                    {
                        "images": "notalist",
                        "captions": "notalist",
                        "footnotes": "notalist",
                        "bbox": {}
                    }
                ]
            }
        ]
    }
    input_file2 = tmp_path / "schema2.json"
    input_file2.write_text(json.dumps(data2), encoding="utf-8")
    res2 = filter_dom(input_file2, remove_bboxes=True)
    assert res2["pages"][2]["articles"][1] == {"images": "notalist", "captions": "notalist", "footnotes": "notalist"}

def test_filter_dom_schema_mismatch2(tmp_path):
    data3 = {
        "pages": [
            {
                "articles": [
                    {
                        "images": [
                            "notadict",
                            {
                                "captions": "notalist",
                                "footnotes": "notalist",
                            }
                        ],
                    }
                ]
            }
        ]
    }
    input_file3 = tmp_path / "schema3.json"
    input_file3.write_text(json.dumps(data3), encoding="utf-8")
    res3 = filter_dom(input_file3, remove_bboxes=True)
    assert res3 == data3

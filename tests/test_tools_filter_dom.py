import json
import pytest
from tools.filter_dom import filter_dom, main

def test_filter_dom_invalid_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        filter_dom(tmp_path / "nonexistent.json", tmp_path / "out.json")

def test_filter_dom_not_json_extension(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello")
    with pytest.raises(ValueError, match=r"\.json"):
        filter_dom(txt_file, tmp_path / "out.json")

def test_filter_dom_invalid_json(tmp_path):
    json_file = tmp_path / "test.json"
    json_file.write_text("invalid json")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(json_file, tmp_path / "out.json")

def test_filter_dom_invalid_schema(tmp_path):
    json_file = tmp_path / "test.json"
    json_file.write_text('{"invalid": "schema"}')
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        filter_dom(json_file, tmp_path / "out.json")

def test_filter_dom_success(tmp_path):
    in_file = tmp_path / "in.json"
    out_file = tmp_path / "out.json"

    valid_data = {
        "document_id": "doc1",
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
        "pages": [
            {
                "page_number": 1,
                "ads": ["ad1"],
                "articles": [
                    {
                        "article_id": "a1",
                        "headline": "h1",
                        "images": [{"path": "img1.png", "media_type": "image", "captions": [], "footnotes": []}],
                        "body_blocks": [],
                        "captions": [],
                        "footnotes": []
                    }
                ],
                "headers": [],
                "footers": [],
                "page_numbers": []
            },
            {
                "page_number": 2,
                "ads": ["ad2"],
                "articles": [],
                "headers": [],
                "footers": [],
                "page_numbers": []
            }
        ]
    }
    in_file.write_text(json.dumps(valid_data))

    filter_dom(in_file, out_file, target_page=1)
    out_data = json.loads(out_file.read_text())
    assert len(out_data["pages"]) == 1
    assert out_data["pages"][0]["page_number"] == 1

    filter_dom(in_file, out_file, remove_ads=True)
    out_data = json.loads(out_file.read_text())
    assert len(out_data["pages"]) == 2
    assert out_data["pages"][0]["ads"] == []
    assert out_data["pages"][1]["ads"] == []

    filter_dom(in_file, out_file, remove_images=True)
    out_data = json.loads(out_file.read_text())
    assert out_data["pages"][0]["articles"][0]["images"] == []

def test_main_success(tmp_path, capsys):
    in_file = tmp_path / "in.json"
    out_file = tmp_path / "out.json"

    valid_data = {
        "document_id": "doc1",
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
        "pages": []
    }
    in_file.write_text(json.dumps(valid_data))

    main([str(in_file), "-o", str(out_file)])

    captured = capsys.readouterr()
    assert "successfully written" in captured.out

def test_main_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["nonexistent.json", "-o", str(tmp_path / "out.json")])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Error filtering JSON file" in captured.err

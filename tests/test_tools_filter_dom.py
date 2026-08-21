import json
import sys
from pathlib import Path
import pytest
from tools.filter_dom import filter_dom, main
import runpy

@pytest.fixture
def valid_json_data():
    return {
        "document_id": "test-doc-123",
        "pages": [
            {
                "page_number": 1,
                "ads": ["Ad 1", "Ad 2"],
                "articles": [
                    {
                        "article_id": "art-1",
                        "headline": "Test Headline 1",
                        "body_blocks": ["Block 1"],
                        "images": [{"path": "img1.jpg", "captions": [{"text": "Cap 1"}], "footnotes": [{"text": "Foot 1"}]}],
                        "captions": [{"text": "Cap 1"}],
                        "footnotes": [{"text": "Foot 1"}]
                    },
                    {
                        "article_id": "art-2",
                        "headline": "Skip Me",
                        "body_blocks": ["Block 2"]
                    }
                ]
            },
            {
                "page_number": 2,
                "articles": [
                    {
                        "article_id": "art-3",
                        "headline": "Test Headline 2"
                    }
                ]
            }
        ]
    }

def test_filter_dom_valid(tmp_path, valid_json_data):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(valid_json_data), encoding="utf-8")

    filter_dom(
        json_path=input_file,
        output_path=output_file,
        exclude_pages=[2],
        exclude_ads=True,
        exclude_images=True,
        exclude_headline_pattern=r"Skip"
    )

    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(output_data["pages"]) == 1
    page1 = output_data["pages"][0]
    assert page1["page_number"] == 1
    assert page1["ads"] == []
    assert len(page1["articles"]) == 1
    art1 = page1["articles"][0]
    assert art1["headline"] == "Test Headline 1"
    assert "images" not in art1 or art1["images"] == []
    assert "captions" not in art1 or art1["captions"] == []
    assert "footnotes" not in art1 or art1["footnotes"] == []

def test_filter_dom_invalid_file_not_found(tmp_path):
    output_file = tmp_path / "output.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        filter_dom(Path("non_existent.json"), output_file)

def test_filter_dom_invalid_extension(tmp_path):
    input_file = tmp_path / "input.txt"
    input_file.write_text("{}", encoding="utf-8")
    output_file = tmp_path / "output.json"
    with pytest.raises(ValueError, match="must be a \\.json file"):
        filter_dom(input_file, output_file)

def test_filter_dom_invalid_json(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text("{invalid json}", encoding="utf-8")
    output_file = tmp_path / "output.json"
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(input_file, output_file)

def test_filter_dom_no_pages(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text('{"document_id": "test"}', encoding="utf-8")
    output_file = tmp_path / "output.json"
    with pytest.raises(ValueError, match="No 'pages' field found"):
        filter_dom(input_file, output_file)

def test_main_valid(tmp_path, valid_json_data, capsys):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(valid_json_data), encoding="utf-8")

    main([str(input_file), str(output_file)])

    captured = capsys.readouterr()
    assert "Successfully filtered DOM" in captured.out

def test_main_error(tmp_path, capsys):
    output_file = tmp_path / "output.json"
    with pytest.raises(SystemExit) as exc:
        main(["non_existent.json", str(output_file)])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err

def test_main_block():
    sys.modules.pop("tools.filter_dom", None)
    sys.argv = ["filter_dom.py", "in.json", "out.json"]
    try:
        runpy.run_module("tools.filter_dom", run_name="__main__")
    except SystemExit:
        pass

def test_filter_dom_no_headline_pattern(tmp_path, valid_json_data):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(valid_json_data), encoding="utf-8")

    filter_dom(
        json_path=input_file,
        output_path=output_file,
    )

    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(output_data["pages"]) == 2

def test_filter_dom_missing_image_keys(tmp_path, valid_json_data):
    # Test branch where image/caption/footnote doesn't exist but exclude_images is True
    valid_json_data["pages"][1]["articles"][0]["images"] = []
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(valid_json_data), encoding="utf-8")

    filter_dom(
        json_path=input_file,
        output_path=output_file,
        exclude_images=True
    )

    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(output_data["pages"]) == 2

def test_filter_dom_no_articles_in_page(tmp_path, valid_json_data):
    # Test branch where a page doesn't have an 'articles' key
    del valid_json_data["pages"][0]["articles"]
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(valid_json_data), encoding="utf-8")

    filter_dom(
        json_path=input_file,
        output_path=output_file,
    )

    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "articles" not in output_data["pages"][0]

import json
import sys

import pytest

from tools.anonymize_dom import main, anonymize_dom


def test_anonymize_dom_success(tmp_path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "ads": ["Ad text 1", "Ad 2"],
                "headers": ["Header 1"],
                "footers": ["Footer 1"],
                "articles": [
                    {
                        "article_id": "a1",
                        "headline": "Headline Text",
                        "body_blocks": ["Body 1", "Body 2"],
                        "captions": [{"text": "Caption 1"}],
                        "footnotes": [{"text": "Footnote 1"}],
                        "images": [
                            {
                                "path": "img1.png",
                                "captions": [{"text": "Img Caption"}],
                                "footnotes": [{"text": "Img Footnote"}],
                            }
                        ],
                    }
                ],
            }
        ],
        "quality": {"status": "success", "parser": "mineru"},
    }
    input_file.write_text(json.dumps(data))

    anonymize_dom(input_file, output_file)

    assert output_file.exists()
    out_data = json.loads(output_file.read_text())
    page = out_data["pages"][0]

    assert page["ads"] == ["*" * 9, "*" * 4]
    assert page["headers"] == ["*" * 8]
    assert page["footers"] == ["*" * 8]

    article = page["articles"][0]
    assert article["headline"] == "*" * 13
    assert article["body_blocks"] == ["*" * 6, "*" * 6]
    assert article["captions"][0]["text"] == "*" * 9
    assert article["footnotes"][0]["text"] == "*" * 10

    image = article["images"][0]
    assert image["captions"][0]["text"] == "*" * 11
    assert image["footnotes"][0]["text"] == "*" * 12


def test_anonymize_dom_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="File not found"):
        anonymize_dom(tmp_path / "nonexistent.json", tmp_path / "out.json")


def test_anonymize_dom_invalid_extension(tmp_path):
    input_file = tmp_path / "input.txt"
    input_file.touch()
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        anonymize_dom(input_file, tmp_path / "out.json")


def test_anonymize_dom_invalid_json(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text("not json")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        anonymize_dom(input_file, tmp_path / "out.json")


def test_anonymize_dom_schema_validation_error(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps({"invalid": "data"}))
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        anonymize_dom(input_file, tmp_path / "out.json")


def test_main_success(tmp_path, monkeypatch, capsys):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "out.json"
    data = {
        "document_id": "test_doc",
        "pages": [
            {"page_number": 1, "articles": [{"article_id": "a1", "headline": "H1"}]}
        ],
        "quality": {"status": "success"},
    }
    input_file.write_text(json.dumps(data))

    main([str(input_file), "-o", str(output_file)])
    captured = capsys.readouterr()
    assert "Anonymized JSON successfully written" in captured.out


def test_main_error(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([str(tmp_path / "nonexistent.json"), "-o", str(tmp_path / "out.json")])
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error anonymizing JSON file: File not found" in captured.err


def test_sys_path_injection_anon(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "path", [])
    import runpy

    runpy.run_path("tools/anonymize_dom.py")

from pathlib import Path
import json
import sys

import pytest

from tools.find_replace_dom import main, find_replace_dom


def test_find_replace_dom_success(tmp_path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "ads": ["Ad TARGET text", "Ad 2"],
                "headers": ["Header TARGET"],
                "footers": ["Footer 1"],
                "page_numbers": ["1"],
                "articles": [
                    {
                        "article_id": "a1",
                        "headline": "Headline TARGET Text",
                        "body_blocks": ["Body TARGET", "Body 2"],
                        "captions": [{"text": "Caption TARGET"}],
                        "footnotes": [{"text": "Footnote 1"}],
                        "images": [
                            {
                                "path": "img1.png",
                                "captions": [{"text": "Img Caption TARGET"}],
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

    find_replace_dom(input_file, output_file, "TARGET", "REPLACED")

    assert output_file.exists()
    out_data = json.loads(output_file.read_text())
    page = out_data["pages"][0]

    assert page["ads"] == ["Ad REPLACED text", "Ad 2"]
    assert page["headers"] == ["Header REPLACED"]
    assert page["footers"] == ["Footer 1"]
    assert page["page_numbers"] == ["1"]

    article = page["articles"][0]
    assert article["headline"] == "Headline REPLACED Text"
    assert article["body_blocks"] == ["Body REPLACED", "Body 2"]
    assert article["captions"][0]["text"] == "Caption REPLACED"
    assert article["footnotes"][0]["text"] == "Footnote 1"

    image = article["images"][0]
    assert image["captions"][0]["text"] == "Img Caption REPLACED"
    assert image["footnotes"][0]["text"] == "Img Footnote"


def test_find_replace_dom_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="File not found"):
        find_replace_dom(tmp_path / "nonexistent.json", tmp_path / "out.json", "A", "B")


def test_find_replace_dom_invalid_extension(tmp_path):
    input_file = tmp_path / "input.txt"
    input_file.touch()
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        find_replace_dom(input_file, tmp_path / "out.json", "A", "B")


def test_find_replace_dom_invalid_json(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text("not json")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        find_replace_dom(input_file, tmp_path / "out.json", "A", "B")


def test_find_replace_dom_schema_validation_error(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps({"invalid": "data"}))
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        find_replace_dom(input_file, tmp_path / "out.json", "A", "B")


def test_main_success(tmp_path, monkeypatch, capsys):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "out.json"
    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [{"article_id": "a1", "headline": "H1 TARGET H1"}],
            }
        ],
        "quality": {"status": "success"},
    }
    input_file.write_text(json.dumps(data))

    main([str(input_file), "TARGET", "REPLACED", "-o", str(output_file)])
    captured = capsys.readouterr()
    assert "Updated JSON successfully written" in captured.out


def test_main_error(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                str(tmp_path / "nonexistent.json"),
                "A",
                "B",
                "-o",
                str(tmp_path / "out.json"),
            ]
        )
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error updating JSON file: File not found" in captured.err


def test_sys_path_injection_find_replace(tmp_path, monkeypatch):
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    monkeypatch.setattr(sys, "path", [path for path in sys.path if path != src_path])
    import runpy

    runpy.run_path("tools/find_replace_dom.py")

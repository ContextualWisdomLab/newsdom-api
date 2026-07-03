from __future__ import annotations

import json

import pytest
from tools import extract_text


@pytest.fixture
def mock_json_data() -> dict:
    return {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "headers": ["Header 1", "Header 2"],
                "articles": [
                    {
                        "article_id": "art_1",
                        "headline": "Headline 1",
                        "body_blocks": ["Body paragraph 1.", "Body paragraph 2."],
                        "images": [
                            {
                                "path": "img1.jpg",
                                "captions": [{"text": "Image Caption 1"}],
                                "footnotes": [{"text": "Image Footnote 1"}],
                            }
                        ],
                        "captions": [{"text": "Article Caption 1"}],
                        "footnotes": [{"text": "Article Footnote 1"}],
                    }
                ],
                "ads": ["Ad text 1"],
                "footers": ["Footer 1"],
            },
            {
                "page_number": 2,
                "articles": [{"headline": "", "body_blocks": ["", "Only this block."]}],
            },
            "invalid_page_type",
        ],
    }


def test_extract_plain_text(mock_json_data):
    result = extract_text.extract_plain_text(mock_json_data)

    assert "Header 1" in result
    assert "Header 2" in result
    assert "Headline 1" in result
    assert "Body paragraph 1." in result
    assert "Body paragraph 2." in result
    assert "Image Caption 1" in result
    assert "Image Footnote 1" in result
    assert "Article Caption 1" in result
    assert "Article Footnote 1" in result
    assert "Ad text 1" in result
    assert "Footer 1" in result
    assert "Only this block." in result
    assert "invalid_page_type" not in result

    # Check that double newlines exist
    assert "Header 1\n\nHeader 2" in result


def test_extract_plain_text_empty():
    assert extract_text.extract_plain_text({}) == ""


def test_main_stdout(tmp_path, mock_json_data, capsys):
    json_path = tmp_path / "test.json"
    json_path.write_text(json.dumps(mock_json_data), encoding="utf-8")

    extract_text.main([str(json_path)])
    out = capsys.readouterr().out
    assert "Headline 1" in out
    assert "Body paragraph 1." in out


def test_main_file_output(tmp_path, mock_json_data, capsys):
    json_path = tmp_path / "test.json"
    json_path.write_text(json.dumps(mock_json_data), encoding="utf-8")
    out_path = tmp_path / "out.txt"

    extract_text.main([str(json_path), "-o", str(out_path)])

    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Headline 1" in content
    assert "Body paragraph 1." in content

    out = capsys.readouterr().out
    assert "Text extracted and written to" in out


def test_main_error(tmp_path, capsys):
    missing_path = tmp_path / "missing.json"
    with pytest.raises(SystemExit) as e:
        extract_text.main([str(missing_path)])

    assert e.value.code == 1
    assert "Error extracting text:" in capsys.readouterr().err


def test_extract_plain_text_branches():
    from tools.extract_text import extract_plain_text

    # Test dictionary bypass branches inside loops
    data = {
        "pages": [
            "not a dict",
            {
                "articles": [
                    "not a dict",
                    {
                        "images": ["not a dict", {"captions": [{}], "footnotes": [{}]}],
                        "captions": [{}],
                        "footnotes": [{}],
                    },
                ]
            },
        ]
    }
    assert extract_plain_text(data) == ""


def test_caption_text_string():
    from tools.extract_text import _caption_text

    assert _caption_text("string caption") == "string caption"

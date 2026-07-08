from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import export_html


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample.json"
    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "headers": ["Header 1"],
                "articles": [
                    {
                        "headline": "Article 1",
                        "body_blocks": ["Body 1"],
                        "images": [
                            {"path": "img1.png", "captions": [{"text": "Cap 1"}]}
                        ],
                        "captions": ["Caption string", {"text": "Caption dict"}],
                        "footnotes": ["Footnote 1"],
                    },
                    "invalid_article_type",
                ],
                "ads": ["Ad 1"],
                "footers": ["Footer 1"],
                "page_numbers": ["1"],
            },
            "invalid_page_type",
        ],
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_export_html_stdout(mock_json_file, capsys):
    export_html.main([str(mock_json_file)])
    out = capsys.readouterr().out
    assert "<h1>Document: test_doc</h1>" in out
    assert "<h2>Page 1</h2>" in out
    assert "<li>Header 1</li>" in out
    assert "<h3>Article: Article 1</h3>" in out
    assert "<p>Body 1</p>" in out
    assert '<img src="img1.png"' in out
    assert "<figcaption>Caption: Cap 1</figcaption>" in out
    assert "<p>Caption: Caption string</p>" in out
    assert "<p>Caption: Caption dict</p>" in out
    assert "<p>Footnote: Footnote 1</p>" in out
    assert "<li>Ad 1</li>" in out
    assert "<li>Footer 1</li>" in out
    assert "<h3>Page Numbers</h3>" in out
    assert "<li>1</li>" in out
    assert "invalid_article_type" not in out
    assert "invalid_page_type" not in out


def test_export_html_file(mock_json_file, tmp_path):
    out_file = tmp_path / "out.html"
    export_html.main([str(mock_json_file), "-o", str(out_file)])
    content = out_file.read_text(encoding="utf-8")
    assert "<h1>Document: test_doc</h1>" in content


def test_export_html_empty_data(tmp_path, capsys):
    json_path = tmp_path / "empty.json"
    json_path.write_text(json.dumps({}), encoding="utf-8")
    export_html.main([str(json_path)])
    out = capsys.readouterr().out
    assert "<h1>Document: Unknown Document</h1>" in out


def test_export_html_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        export_html.main([str(tmp_path / "missing.json")])
    assert e.value.code == 1
    assert "Error exporting HTML:" in capsys.readouterr().err


def test_caption_text_helper():
    assert export_html._caption_text({"text": "abc"}) == "abc"
    assert export_html._caption_text("def") == "def"
    assert export_html._caption_text({}) == ""

def test_export_html_missing_fields(tmp_path, capsys):
    json_path = tmp_path / "missing.json"
    data = {
        "pages": [
            {
                "articles": [
                    {
                        "images": [
                            "invalid_image_type"
                        ]
                    }
                ]
            }
        ]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    export_html.main([str(json_path)])
    out = capsys.readouterr().out
    assert "invalid_image_type" not in out

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from tools.export_html import generate_html, main


@pytest.fixture
def sample_json_data() -> dict:
    return {
        "document_id": "test_doc_1",
        "pages": [
            {
                "page_number": 1,
                "headers": ["Top Header < & >"],
                "articles": [
                    {
                        "headline": "Main Article",
                        "body_blocks": ["This is paragraph 1.", "This is paragraph 2."],
                        "images": [
                            {
                                "path": "image1.png",
                                "captions": [{"text": "Image 1 Caption"}],
                            }
                        ],
                        "captions": [{"text": "Article Level Caption"}],
                        "footnotes": [{"text": "Article Footnote 1"}],
                    }
                ],
                "ads": ["Ad Content 1"],
                "footers": ["Bottom Footer"],
                "page_numbers": ["1", "I"],
            },
            {"page_number": 2, "articles": []},
        ],
    }


def test_export_html_success(sample_json_data: dict):
    html = generate_html(sample_json_data)
    assert "<h1>Document: test_doc_1</h1>" in html
    assert "<h2>Page 1</h2>" in html
    assert "<li>Top Header &lt; &amp; &gt;</li>" in html
    assert "<h3>Article: Main Article</h3>" in html
    assert "<p>This is paragraph 1.</p>" in html
    assert "<code>image1.png</code>" in html
    assert "<li>Caption: Image 1 Caption</li>" in html
    assert "<li>Caption: Article Level Caption</li>" in html
    assert "<li>Footnote: Article Footnote 1</li>" in html
    assert "<h3>Advertisements</h3><ul>" in html
    assert "<li>Ad Content 1</li>" in html
    assert "<h3>Footers</h3><ul>" in html
    assert "<li>Bottom Footer</li>" in html
    assert "<h3>Page Numbers</h3><ul>" in html
    assert "<li>1</li>" in html
    assert "<li>I</li>" in html
    assert "<h2>Page 2</h2>" in html


def test_export_html_empty():
    html = generate_html({})
    assert "<h1>Document: Unknown Document</h1>" in html


def test_export_html_invalid_nodes():
    html = generate_html({"pages": ["bad", {"articles": ["bad article"]}]})
    assert "bad" not in html
    assert "<h2>Page Unknown</h2>" in html


def test_export_html_loose_values():
    html = generate_html(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "headline": "Loose Values",
                            "images": [
                                "bad image",
                                {
                                    "path": "photo.png",
                                    "captions": ["plain caption"],
                                },
                            ],
                            "captions": ["article caption"],
                        },
                        {"headline": "Only Footnotes", "footnotes": ["plain footnote"]},
                    ]
                }
            ]
        }
    )
    assert "bad image" not in html
    assert "<li>Caption: plain caption</li>" in html
    assert "<li>Caption: article caption</li>" in html
    assert "<li>Footnote: plain footnote</li>" in html


def test_export_html_main_stdout(tmp_path: Path, sample_json_data: dict, capsys: pytest.CaptureFixture):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")
    main([str(input_file)])
    assert "<h1>Document: test_doc_1</h1>" in capsys.readouterr().out


def test_export_html_main_file_output(tmp_path: Path, sample_json_data: dict, capsys: pytest.CaptureFixture):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")
    output_file = tmp_path / "output.html"

    main([str(input_file), "-o", str(output_file)])
    assert output_file.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
    assert f"HTML written to {output_file}" in capsys.readouterr().out


def test_export_html_main_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture):
    input_file = tmp_path / "missing.json"
    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file)])
    assert excinfo.value.code == 1
    assert "Error: [Errno 2] No such file or directory" in capsys.readouterr().err


def test_export_html_main_invalid_json(tmp_path: Path, capsys: pytest.CaptureFixture):
    input_file = tmp_path / "input.json"
    input_file.write_text("invalid json", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file)])
    assert excinfo.value.code == 1
    assert "Error: Invalid JSON" in capsys.readouterr().err


def test_export_html_main_oserror(tmp_path: Path, sample_json_data: dict, capsys: pytest.CaptureFixture):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")
    output_file = tmp_path / "output.html"

    with patch("pathlib.Path.write_text", side_effect=OSError("Mocked OSError")):
        with pytest.raises(SystemExit) as excinfo:
            main([str(input_file), "-o", str(output_file)])

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "Error exporting HTML: Mocked OSError" in err

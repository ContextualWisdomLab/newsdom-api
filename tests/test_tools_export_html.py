from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.export_html import generate_html, main


@pytest.fixture
def sample_json_data() -> dict[str, object]:
    return {
        "document_id": "test_doc_1 & < >",
        "pages": [
            {
                "page_number": 1,
                "headers": ["Top Header & More"],
                "articles": [
                    {
                        "headline": "Main Article <Test>",
                        "body_blocks": [
                            "This is paragraph 1.",
                            "This is paragraph 2 & stuff.",
                        ],
                        "images": [
                            {
                                "path": "image1.png",
                                "captions": [{"text": "Image 1 Caption &"}],
                            }
                        ],
                        "captions": [{"text": "Article Level Caption"}],
                        "footnotes": [{"text": "Article Footnote 1"}],
                    }
                ],
                "ads": ["Ad Content 1 & Co."],
                "footers": ["Bottom Footer"],
                "page_numbers": ["1", "I"],
            },
            {"page_number": 2, "articles": []},
        ],
    }


def test_generate_html(sample_json_data: dict[str, object]) -> None:
    html_out = generate_html(sample_json_data)

    # Document Title and Headings (escaped)
    assert "<title>test_doc_1 &amp; &lt; &gt;</title>" in html_out
    assert "<h1>Document: test_doc_1 &amp; &lt; &gt;</h1>" in html_out

    # Page and Header
    assert "<h2>Page 1</h2>" in html_out
    assert "<strong>Header:</strong> Top Header &amp; More" in html_out

    # Article
    assert '<h3 class="article-headline">Main Article &lt;Test&gt;</h3>' in html_out
    assert '<p class="body-block">This is paragraph 1.</p>' in html_out
    assert '<p class="body-block">This is paragraph 2 &amp; stuff.</p>' in html_out

    # Images and Captions
    assert "<code>image1.png</code>" in html_out
    assert "Caption: Image 1 Caption &amp;" in html_out
    assert "Caption: Article Level Caption" in html_out
    assert "Footnote: Article Footnote 1" in html_out

    # Ads, Footers, Page Numbers
    assert '<div class="ad-block">Ad Content 1 &amp; Co.</div>' in html_out
    assert "Bottom Footer</div>" in html_out
    assert "Page No: I</span>" in html_out

    # Empty Page
    assert "<h2>Page 2</h2>" in html_out

    assert html_out.endswith("</html>\n")


def test_generate_html_empty_data() -> None:
    html_out = generate_html({})

    assert "<h1>Document: Unknown Document</h1>" in html_out


def test_generate_html_skips_non_dict_nodes() -> None:
    html_out = generate_html({"pages": ["bad", {"articles": ["bad article"]}]})

    assert "bad article" not in html_out
    assert "<h2>Page Unknown</h2>" in html_out


def test_generate_html_handles_loose_caption_and_image_values() -> None:
    html_out = generate_html(
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
                                    "captions": ["plain caption &"],
                                },
                            ],
                            "captions": ["article caption <"],
                        },
                        {
                            "headline": "Only Footnotes",
                            "footnotes": ["plain footnote >"],
                        },
                    ]
                }
            ]
        }
    )

    assert "bad image" not in html_out
    assert "Caption: plain caption &amp;" in html_out
    assert "Caption: article caption &lt;" in html_out
    assert "Footnote: plain footnote &gt;" in html_out


def test_main_stdout(
    tmp_path: Path,
    sample_json_data: dict[str, object],
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")

    main([str(input_file)])

    captured = capsys.readouterr()
    assert "<h1>Document: test_doc_1 &amp; &lt; &gt;</h1>" in captured.out


def test_main_file_output(
    tmp_path: Path,
    sample_json_data: dict[str, object],
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")
    output_file = tmp_path / "output.html"

    main([str(input_file), "-o", str(output_file)])

    assert "<h1>Document: test_doc_1 &amp; &lt; &gt;</h1>" in output_file.read_text(
        encoding="utf-8"
    )
    assert f"HTML written to {output_file}" in capsys.readouterr().out


def test_main_invalid_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text("invalid json", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file)])

    assert excinfo.value.code == 1
    assert "Error exporting HTML" in capsys.readouterr().err


def test_main_file_output_error(
    tmp_path: Path,
    sample_json_data: dict[str, object],
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")
    output_file = tmp_path / "nonexistent" / "output.html"

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), "-o", str(output_file)])

    assert excinfo.value.code == 1
    assert "Error exporting HTML" in capsys.readouterr().err


def test_module_main() -> None:
    import runpy
    import sys
    from unittest.mock import patch

    sys.modules.pop("tools.export_html", None)
    with patch("sys.argv", ["tools/export_html.py", "-h"]):
        try:
            runpy.run_module("tools.export_html", run_name="__main__")
        except SystemExit as excinfo:
            assert excinfo.code == 0

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.export_html import generate_html, main


@pytest.fixture
def sample_json_data() -> dict[str, object]:
    return {
        "document_id": "test_doc_1 & < >",
        "quality": {
            "status": "success",
            "parser": "mineru",
            "warnings": ["Low confidence & bad"],
        },
        "pages": [
            {
                "page_number": 1,
                "width": 800.0,
                "height": 1200.0,
                "headers": ["Top Header & More"],
                "articles": [
                    {
                        "headline": "Main Article <Test>",
                        "bbox": {"x0": 10, "y0": 20, "x1": 30, "y1": 40},
                        "body_blocks": [
                            "This is paragraph 1.",
                            "This is paragraph 2 & stuff.",
                        ],
                        "images": [
                            {
                                "path": "image1.png",
                                "media_type": "figure",
                                "bbox": {"x0": 1, "y0": 2, "x1": 3, "y1": 4},
                                "captions": [
                                    {
                                        "text": "Image 1 Caption &",
                                        "bbox": {"x0": 5, "y0": 6, "x1": 7, "y1": 8},
                                    }
                                ],
                            }
                        ],
                        "captions": [
                            {
                                "text": "Article Level Caption",
                                "bbox": {"x0": 100, "y0": 200, "x1": 300, "y1": 400},
                            }
                        ],
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

    # Quality Block
    assert "<strong>Parse Status:</strong> success (Parser: mineru)" in html_out
    assert "<li>Low confidence &amp; bad</li>" in html_out

    # Page and Header
    assert "<h2>Page 1</h2>" in html_out
    assert '<div class="dimensions">Dimensions: 800.0 x 1200.0</div>' in html_out
    assert "<strong>Header:</strong> Top Header &amp; More" in html_out

    # Article
    assert '<h3 class="article-headline">Main Article &lt;Test&gt;</h3>' in html_out
    assert (
        '<div class="bbox">Bounding Box: (x0: 10, y0: 20, x1: 30, y1: 40)</div>'
        in html_out
    )
    assert '<p class="body-block">This is paragraph 1.</p>' in html_out
    assert '<p class="body-block">This is paragraph 2 &amp; stuff.</p>' in html_out

    # Images and Captions
    assert "<code>image1.png</code>" in html_out
    assert '<span class="media-type">figure</span>' in html_out
    assert '<span class="bbox">[BBox: (x0: 1, y0: 2, x1: 3, y1: 4)]</span>' in html_out
    assert "Caption: Image 1 Caption &amp;" in html_out
    assert '<span class="bbox">[BBox: (x0: 5, y0: 6, x1: 7, y1: 8)]</span>' in html_out

    assert "Caption: Article Level Caption" in html_out
    assert (
        '<span class="bbox">[BBox: (x0: 100, y0: 200, x1: 300, y1: 400)]</span>'
        in html_out
    )

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

def test_generate_html_bbox_missing():
    html_out = generate_html({"pages": [{"articles": [{"images": [{"path": "img", "bbox": {"x0": 1, "y0": 1, "x1": 1}}], "captions": [{"text": "cap", "bbox": {"x0": 1, "y0": 1, "x1": 1}}]}]}]})
    assert html_out

def test_generate_html_bbox_none():
    html_out = generate_html({"pages": [{"articles": [{"images": [{"path": "img", "bbox": None}], "captions": [{"text": "cap", "bbox": None}]}]}]})
    assert html_out

def test_generate_html_invalid_bbox_values():
    html_out = generate_html({"pages": [{"articles": [{"images": [{"path": "img", "bbox": {"x0": None, "y0": None, "x1": None, "y1": None}}], "captions": [{"text": "cap", "bbox": {"x0": None, "y0": None, "x1": None, "y1": None}}]}]}]})
    assert html_out

def test_generate_html_missing_dims():
    html_out = generate_html({"pages": [{"width": None, "height": None, "articles": []}]})
    assert html_out

def test_generate_html_quality_no_warnings():
    html_out = generate_html({"quality": {"status": "success", "parser": "mineru", "warnings": []}})
    assert html_out

def test_generate_html_empty_caption_bbox():
    html_out = generate_html({"pages": [{"articles": [{"captions": [{"text": "cap", "bbox": None}]}]}]})
    assert html_out

def test_generate_html_bbox_not_dict():
    html_out = generate_html({"pages": [{"articles": [{"images": [{"path": "img", "bbox": "not_a_dict"}], "captions": [{"text": "cap", "bbox": "not_a_dict"}]}]}]})
    assert html_out

def test_generate_html_caption_dict_no_bbox():
    html_out = generate_html({"pages": [{"articles": [{"captions": [{"text": "cap"}]}]}]})
    assert html_out

def test_generate_html_article_bbox():
    # test article with bbox, and one with none
    html_out = generate_html({"pages": [{"articles": [{"headline": "A1", "bbox": {"x0": 1, "y0": 2, "x1": 3, "y1": 4}}, {"headline": "A2", "bbox": None}]}]})
    assert html_out

def test_generate_html_article_captions():
    # test article captions loop missing bbox branch
    html_out = generate_html({"pages": [{"articles": [{"captions": [{"text": "cap", "bbox": {"x0": 1, "y0": 2, "x1": 3, "y1": 4}}], "images": []}]}]})
    assert html_out

def test_generate_html_headers_dict():
    html_out = generate_html({"pages": [{"headers": [{"text": "header1"}]}]})
    assert html_out

def test_generate_html_caption_bbox_missing_coords():
    html_out = generate_html({"pages": [{"articles": [{"captions": [{"text": "cap", "bbox": {"x0": 1, "y0": 2}}], "images": []}]}]})
    assert html_out

def test_generate_html_image_caption_bbox_missing_coords():
    html_out = generate_html({"pages": [{"articles": [{"images": [{"path": "img1", "captions": [{"text": "cap", "bbox": {"x0": 1, "y0": 2}}]}], "captions": []}]}]})
    assert html_out

def test_generate_html_article_not_dict():
    html_out = generate_html({"pages": [{"articles": ["not a dict"]}]})
    assert html_out

def test_generate_html_image_not_dict():
    html_out = generate_html({"pages": [{"articles": [{"images": ["not a dict"]}]}]})
    assert html_out

def test_generate_html_headers_empty_iterable():
    html_out = generate_html({"pages": [{"headers": (h for h in [])}]})
    assert html_out

def test_generate_html_captions_empty_iterable():
    html_out = generate_html({"pages": [{"articles": [{"captions": (c for c in [])}]}]})
    assert html_out

def test_generate_html_headers_generator():
    html_out = generate_html({"pages": [{"headers": (h for h in ["header1"])}]})
    assert html_out

def test_generate_html_captions_generator():
    html_out = generate_html({"pages": [{"articles": [{"captions": (c for c in [{"text": "cap"}])}]}]})
    assert html_out

def test_generate_html_headers_gen_empty():
    html_out = generate_html({"pages": [{"headers": (h for h in [])}]})
    assert html_out

def test_generate_html_captions_gen_empty():
    html_out = generate_html({"pages": [{"articles": [{"captions": (c for c in [])}]}]})
    assert html_out

class TrueButEmpty:
    def __bool__(self):
        return True
    def __iter__(self):
        return iter([])

def test_generate_html_headers_true_empty_iterable():
    html_out = generate_html({"pages": [{"headers": TrueButEmpty()}]})
    assert html_out

def test_generate_html_captions_true_empty_iterable():
    html_out = generate_html({"pages": [{"articles": [{"captions": TrueButEmpty()}]}]})
    assert html_out

def test_generate_html_empty_bbox_str():
    # Covers article.bbox -> empty str (114->117)
    # Covers image.captions.bbox -> cap_bbox = None (140->146)
    # Covers image.captions.bbox -> cap_bbox_str empty
    html_out = generate_html({"pages": [{"articles": [{
        "headline": "A",
        "bbox": {"x0": None}, # Missing y0, so bbox_str is ""
        "images": [{"path": "img", "captions": [{"text": "cap", "bbox": None}, {"text": "cap2", "bbox": {"x0": None}}]}]
    }]}]})
    assert html_out

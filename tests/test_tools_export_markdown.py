from __future__ import annotations

import json

import pytest
from tools.export_markdown import generate_markdown, main


@pytest.fixture
def sample_json_data() -> dict[str, object]:
    return {
        "document_id": "test_doc_1",
        "quality": {
            "status": "success",
            "parser": "mineru",
            "warnings": ["Low confidence"],
        },
        "pages": [
            {
                "page_number": 1,
                "width": 800.0,
                "height": 1200.0,
                "headers": ["Top Header"],
                "articles": [
                    {
                        "headline": "Main Article",
                        "bbox": {"x0": 10, "y0": 20, "x1": 30, "y1": 40},
                        "body_blocks": ["This is paragraph 1.", "This is paragraph 2."],
                        "images": [
                            {
                                "path": "image1.png",
                                "media_type": "figure",
                                "bbox": {"x0": 1, "y0": 2, "x1": 3, "y1": 4},
                                "captions": [
                                    {
                                        "text": "Image 1 Caption",
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
                "ads": ["Ad Content 1"],
                "footers": ["Bottom Footer"],
                "page_numbers": ["1", "I"],
            },
            {"page_number": 2, "articles": []},
        ],
    }


def test_generate_markdown(sample_json_data):
    markdown = generate_markdown(sample_json_data)

    assert "# Document: test_doc_1" in markdown
    assert "**Parse Status**: success (Parser: mineru)" in markdown
    assert "**Warnings**:" in markdown
    assert "- Low confidence" in markdown
    assert "## Page 1" in markdown
    assert "**Dimensions**: 800.0 x 1200.0" in markdown
    assert "### Headers" in markdown
    assert "- Top Header" in markdown
    assert "### Article: Main Article" in markdown
    assert "**Bounding Box**: (x0: 10, y0: 20, x1: 30, y1: 40)" in markdown
    assert "This is paragraph 1." in markdown
    assert "This is paragraph 2." in markdown
    assert (
        "**Image 1**: `image1.png` (Type: figure) [BBox: (x0: 1, y0: 2, x1: 3, y1: 4)]"
        in markdown
    )
    assert (
        "  - Caption: Image 1 Caption [BBox: (x0: 5, y0: 6, x1: 7, y1: 8)]" in markdown
    )
    assert (
        "- Caption: Article Level Caption [BBox: (x0: 100, y0: 200, x1: 300, y1: 400)]"
        in markdown
    )
    assert "- Footnote: Article Footnote 1" in markdown
    assert "### Advertisements" in markdown
    assert "- Ad Content 1" in markdown
    assert "### Footers" in markdown
    assert "- Bottom Footer" in markdown
    assert "### Page Numbers" in markdown
    assert "- I" in markdown
    assert "## Page 2" in markdown
    assert markdown.endswith("\n")


def test_generate_markdown_empty_data():
    markdown = generate_markdown({})

    assert markdown == "# Document: Unknown Document\n"


def test_generate_markdown_skips_non_dict_nodes():
    markdown = generate_markdown({"pages": ["bad", {"articles": ["bad article"]}]})

    assert "bad" not in markdown
    assert "## Page Unknown" in markdown


def test_generate_markdown_handles_loose_caption_and_image_values():
    markdown = generate_markdown(
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

    assert "bad image" not in markdown
    assert "  - Caption: plain caption" in markdown
    assert "- Caption: article caption" in markdown
    assert "- Footnote: plain footnote" in markdown


def test_main_stdout(tmp_path, sample_json_data, capsys):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")

    main([str(input_file)])

    captured = capsys.readouterr()
    assert "# Document: test_doc_1" in captured.out


def test_main_file_output(tmp_path, sample_json_data, capsys):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")
    output_file = tmp_path / "output.md"

    main([str(input_file), "-o", str(output_file)])

    assert output_file.read_text(encoding="utf-8").startswith("# Document: test_doc_1")
    assert f"Markdown written to {output_file}" in capsys.readouterr().out


def test_main_invalid_input(tmp_path, capsys):
    input_file = tmp_path / "input.json"
    input_file.write_text("invalid json", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file)])

    assert excinfo.value.code == 1
    assert "Error exporting Markdown" in capsys.readouterr().err


def test_main_file_output_error(tmp_path, sample_json_data, capsys):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")
    output_file = tmp_path / "nonexistent" / "output.md"

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), "-o", str(output_file)])

    assert excinfo.value.code == 1
    assert "Error exporting Markdown" in capsys.readouterr().err


def test_generate_markdown_bbox_missing():
    md_out = generate_markdown(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "images": [
                                {"path": "img", "bbox": {"x0": 1, "y0": 1, "x1": 1}}
                            ],
                            "captions": [
                                {"text": "cap", "bbox": {"x0": 1, "y0": 1, "x1": 1}}
                            ],
                        }
                    ]
                }
            ]
        }
    )
    assert md_out


def test_generate_markdown_bbox_none():
    md_out = generate_markdown(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "images": [{"path": "img", "bbox": None}],
                            "captions": [{"text": "cap", "bbox": None}],
                        }
                    ]
                }
            ]
        }
    )
    assert md_out


def test_generate_markdown_invalid_bbox_values():
    md_out = generate_markdown(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "images": [
                                {
                                    "path": "img",
                                    "bbox": {
                                        "x0": None,
                                        "y0": None,
                                        "x1": None,
                                        "y1": None,
                                    },
                                }
                            ],
                            "captions": [
                                {
                                    "text": "cap",
                                    "bbox": {
                                        "x0": None,
                                        "y0": None,
                                        "x1": None,
                                        "y1": None,
                                    },
                                }
                            ],
                        }
                    ]
                }
            ]
        }
    )
    assert md_out


def test_generate_markdown_missing_dims():
    md_out = generate_markdown(
        {"pages": [{"width": None, "height": None, "articles": []}]}
    )
    assert md_out


def test_generate_markdown_quality_no_warnings():
    md_out = generate_markdown(
        {"quality": {"status": "success", "parser": "mineru", "warnings": []}}
    )
    assert md_out


def test_generate_markdown_empty_caption_bbox():
    md_out = generate_markdown(
        {"pages": [{"articles": [{"captions": [{"text": "cap", "bbox": None}]}]}]}
    )
    assert md_out


def test_generate_markdown_bbox_not_dict():
    md_out = generate_markdown(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "images": [{"path": "img", "bbox": "not_a_dict"}],
                            "captions": [{"text": "cap", "bbox": "not_a_dict"}],
                        }
                    ]
                }
            ]
        }
    )
    assert md_out


def test_generate_markdown_caption_dict_no_bbox():
    md_out = generate_markdown(
        {"pages": [{"articles": [{"captions": [{"text": "cap"}]}]}]}
    )
    assert md_out


def test_generate_markdown_article_bbox():
    md_out = generate_markdown(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "headline": "A1",
                            "bbox": {"x0": 1, "y0": 2, "x1": 3, "y1": 4},
                        },
                        {"headline": "A2", "bbox": None},
                    ]
                }
            ]
        }
    )
    assert md_out


def test_generate_markdown_article_captions():
    md_out = generate_markdown(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "captions": [
                                {
                                    "text": "cap",
                                    "bbox": {"x0": 1, "y0": 2, "x1": 3, "y1": 4},
                                }
                            ],
                            "images": [],
                        }
                    ]
                }
            ]
        }
    )
    assert md_out


def test_generate_markdown_headers_dict():
    md_out = generate_markdown({"pages": [{"headers": [{"text": "header1"}]}]})
    assert md_out


def test_generate_markdown_caption_bbox_missing_coords():
    md_out = generate_markdown(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "captions": [{"text": "cap", "bbox": {"x0": 1, "y0": 2}}],
                            "images": [],
                        }
                    ]
                }
            ]
        }
    )
    assert md_out


def test_generate_markdown_image_caption_bbox_missing_coords():
    md_out = generate_markdown(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "images": [
                                {
                                    "path": "img1",
                                    "captions": [
                                        {"text": "cap", "bbox": {"x0": 1, "y0": 2}}
                                    ],
                                }
                            ],
                            "captions": [],
                        }
                    ]
                }
            ]
        }
    )
    assert md_out


def test_generate_markdown_article_not_dict():
    md_out = generate_markdown({"pages": [{"articles": ["not a dict"]}]})
    assert md_out


def test_generate_markdown_image_not_dict():
    md_out = generate_markdown({"pages": [{"articles": [{"images": ["not a dict"]}]}]})
    assert md_out


def test_generate_markdown_headers_empty_iterable():
    md_out = generate_markdown({"pages": [{"headers": (h for h in [])}]})
    assert md_out


def test_generate_markdown_captions_empty_iterable():
    md_out = generate_markdown(
        {"pages": [{"articles": [{"captions": (c for c in [])}]}]}
    )
    assert md_out


def test_generate_markdown_headers_generator():
    md_out = generate_markdown({"pages": [{"headers": (h for h in ["header1"])}]})
    assert md_out


def test_generate_markdown_captions_generator():
    md_out = generate_markdown(
        {"pages": [{"articles": [{"captions": (c for c in [{"text": "cap"}])}]}]}
    )
    assert md_out


def test_generate_markdown_headers_gen_empty():
    md_out = generate_markdown({"pages": [{"headers": (h for h in [])}]})
    assert md_out


def test_generate_markdown_captions_gen_empty():
    md_out = generate_markdown(
        {"pages": [{"articles": [{"captions": (c for c in [])}]}]}
    )
    assert md_out


class TrueButEmpty:
    def __bool__(self):
        return True

    def __iter__(self):
        return iter([])


def test_generate_markdown_headers_true_empty_iterable():
    md_out = generate_markdown({"pages": [{"headers": TrueButEmpty()}]})
    assert md_out


def test_generate_markdown_captions_true_empty_iterable():
    md_out = generate_markdown(
        {"pages": [{"articles": [{"captions": TrueButEmpty()}]}]}
    )
    assert md_out


def test_generate_markdown_empty_bbox_str():
    # Covers article.bbox -> empty str
    # Covers image.captions.bbox -> cap_bbox = None
    # Covers image.captions.bbox -> cap_bbox_str empty
    md_out = generate_markdown(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "headline": "A",
                            "bbox": {"x0": None},
                            "images": [
                                {
                                    "path": "img",
                                    "captions": [
                                        {"text": "cap", "bbox": None},
                                        {"text": "cap2", "bbox": {"x0": None}},
                                    ],
                                }
                            ],
                        }
                    ]
                }
            ]
        }
    )
    assert md_out

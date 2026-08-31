from __future__ import annotations

import json

import pytest
from tools.export_markdown import generate_markdown, main


@pytest.fixture
def sample_json_data() -> dict[str, object]:
    return {
        "document_id": "test_doc_1",
        "pages": [
            {
                "page_number": 1,
                "headers": ["Top Header"],
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


def test_generate_markdown(sample_json_data):
    markdown = generate_markdown(sample_json_data)

    assert "# Document: test_doc_1" in markdown
    assert "## Page 1" in markdown
    assert "### Headers" in markdown
    assert "- Top Header" in markdown
    assert "### Article: Main Article" in markdown
    assert "This is paragraph 1." in markdown
    assert "This is paragraph 2." in markdown
    assert "**Image 1**: `image1.png`" in markdown
    assert "  - Caption: Image 1 Caption" in markdown
    assert "- Caption: Article Level Caption" in markdown
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


def test_module_main() -> None:
    import runpy
    import sys
    from unittest.mock import patch

    sys.modules.pop("tools.export_markdown", None)
    with patch("sys.argv", ["tools/export_markdown.py", "-h"]):
        try:
            runpy.run_module("tools.export_markdown", run_name="__main__")
        except SystemExit as excinfo:
            assert excinfo.code == 0

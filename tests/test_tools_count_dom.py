from __future__ import annotations

import json

import pytest
from tools.count_dom import count_elements, main


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


def test_count_elements(sample_json_data):
    counts = count_elements(sample_json_data)

    assert counts["pages"] == 2
    assert counts["articles"] == 1
    assert counts["images"] == 1
    assert counts["body_blocks"] == 2
    assert counts["captions"] == 2  # 1 article caption + 1 image caption
    assert counts["footnotes"] == 1
    assert counts["ads"] == 1
    assert counts["headers"] == 1
    assert counts["footers"] == 1
    assert counts["page_numbers"] == 2


def test_count_elements_empty_data():
    counts = count_elements({})
    assert all(value == 0 for value in counts.values())


def test_count_elements_invalid_pages_type():
    counts = count_elements({"pages": "invalid"})
    assert all(value == 0 for value in counts.values())


def test_count_elements_skips_non_dict_nodes():
    counts = count_elements(
        {"pages": ["bad", {"articles": ["bad article", {"body_blocks": ["block"]}]}]}
    )

    assert counts["pages"] == 1
    assert counts["articles"] == 1
    assert counts["body_blocks"] == 1


def test_count_elements_handles_invalid_types():
    counts = count_elements(
        {
            "pages": [
                {
                    "articles": [
                        {
                            "images": ["bad image"],
                            "body_blocks": "invalid",
                            "captions": "invalid",
                            "footnotes": "invalid",
                        }
                    ],
                    "ads": "invalid",
                    "headers": "invalid",
                    "footers": "invalid",
                    "page_numbers": "invalid",
                }
            ]
        }
    )

    assert counts["images"] == 0
    assert counts["body_blocks"] == 0
    assert counts["captions"] == 0
    assert counts["footnotes"] == 0
    assert counts["ads"] == 0
    assert counts["headers"] == 0
    assert counts["footers"] == 0
    assert counts["page_numbers"] == 0


def test_count_elements_handles_image_invalid_types():
    counts = count_elements(
        {
            "pages": [
                {
                    "articles": [
                        {"images": [{"captions": "invalid", "footnotes": "invalid"}]}
                    ]
                }
            ]
        }
    )

    assert counts["images"] == 1
    assert counts["captions"] == 0
    assert counts["footnotes"] == 0


def test_main_stdout(tmp_path, sample_json_data, capsys):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")

    main([str(input_file)])

    captured = capsys.readouterr()
    assert "pages: 2" in captured.out
    assert "articles: 1" in captured.out


def test_main_invalid_input(tmp_path, capsys):
    input_file = tmp_path / "input.json"
    input_file.write_text("invalid json", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file)])

    assert excinfo.value.code == 1
    assert "Error counting elements" in capsys.readouterr().err


def test_count_elements_invalid_articles_and_images():
    counts = count_elements(
        {"pages": [{"articles": "invalid"}, {"articles": [{"images": "invalid"}]}]}
    )

    assert counts["articles"] == 1
    assert counts["images"] == 0

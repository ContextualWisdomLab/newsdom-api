import json
from pathlib import Path

import pytest

from newsdom_api.dom_builder import (
    MAX_BBOX_COORDINATE,
    MAX_CONTENT_BLOCKS,
    MAX_MEDIA_PATH_LENGTH,
    MAX_PAGE_NUMBER,
    _bbox_from_values,
    _caption_nodes_from_items,
    _coerce_page_number,
    _html_safe_text,
    _new_article,
    _page_number_from_info,
    build_dom,
)


def _load_fixture(name: str):
    return json.loads(Path(f"tests/fixtures/{name}").read_bytes())


def test_build_dom_extracts_articles_from_mineru_sample():
    sample = json.loads(
        Path("tests/fixtures/mineru_sample.json").read_text(encoding="utf-8")
    )
    dom = build_dom(sample, document_id="doc1")
    assert len(dom.pages) == 1
    assert len(dom.pages[0].articles) >= 2
    assert dom.pages[0].articles[0].headline == "次世代電池材料"


def test_bbox_helper_returns_none_for_invalid_values():
    assert _bbox_from_values(None) is None
    assert _bbox_from_values([1, 2, 3]) is None
    assert _bbox_from_values([object(), 0, 1, 1]) is None
    assert _bbox_from_values(["bad", 0, 1, 1]) is None
    assert _bbox_from_values([10**10000, 0, 1, 1]) is None
    assert _bbox_from_values([True, 0, 1, 1]) is None
    assert _bbox_from_values([float("inf"), 0, 1, 1]) is None
    assert _bbox_from_values([-10, -20, -5, -15]) is None
    assert _bbox_from_values([MAX_BBOX_COORDINATE + 1, 0, 1, 1]) is None
    assert _bbox_from_values([5, 0, 1, 1]) is None
    assert _bbox_from_values([0, 5, 1, 1]) is None


def test_build_dom_rejects_oversized_content_list():
    with pytest.raises(ValueError, match="more than"):
        build_dom(
            [{"type": "text", "text": "test"}] * (MAX_CONTENT_BLOCKS + 1),
            document_id="doc-too-large",
        )


def test_build_dom_rejects_non_list_content():
    with pytest.raises(ValueError, match="must be a list"):
        build_dom(("not", "a", "list"), document_id="doc-not-list")


def test_build_dom_handles_non_headline_paths():
    dom = build_dom(
        [
            {
                "type": "text",
                "text": "ignore me",
                "bbox": [0, 0, 10, 10],
                "role": "header",
            },
            {"type": "ad", "text": "buy now", "bbox": [1, 1, 2, 2]},
            {"type": "text", "text": "", "bbox": [1, 1, 2, 2]},
            {
                "type": "image",
                "img_path": "img.png",
                "bbox": [1, 1, 2, 2],
                "image_caption": ["caption"],
            },
            {"type": "table", "table_body": "<table></table>", "bbox": [1, 1, 2, 2]},
            {"type": "text", "text": "body text", "bbox": [1, 1, 2, 2]},
        ],
        document_id="doc2",
    )
    page = dom.pages[0]
    assert page.headers == ["ignore me"]
    assert page.ads == ["buy now"]
    assert page.articles[0].headline == "(untitled)"
    assert page.articles[0].images[0].captions[0].text == "caption"
    assert "&lt;table&gt;&lt;/table&gt;" in page.articles[0].body_blocks
    assert "body text" in page.articles[0].body_blocks


def test_build_dom_escapes_text_fields_for_html_renderers():
    dom = build_dom(
        [
            {
                "type": "text",
                "text": "<script>alert('headline')</script>",
                "text_level": 1,
            },
            {"type": "text", "text": "<img src=x onerror=alert('body')>"},
            {"type": "text", "text": "<b>masthead</b>", "role": "header"},
            {
                "type": "image",
                "img_path": "image.png",
                "image_caption": ["<script>alert('caption')</script>"],
            },
            {"type": "image", "img_path": 'x" onerror="alert(1)'},
            {"type": "table", "table_body": "<script>alert('table')</script>"},
        ],
        document_id="doc-html-safe-text",
    )

    page = dom.pages[0]
    assert page.headers == ["&lt;b&gt;masthead&lt;/b&gt;"]
    assert page.articles[0].headline == (
        "&lt;script&gt;alert(&#x27;headline&#x27;)&lt;/script&gt;"
    )
    assert page.articles[0].body_blocks == [
        "&lt;img src=x onerror=alert(&#x27;body&#x27;)&gt;",
        "&lt;script&gt;alert(&#x27;table&#x27;)&lt;/script&gt;",
    ]
    assert page.articles[0].images[0].captions[0].text == (
        "&lt;script&gt;alert(&#x27;caption&#x27;)&lt;/script&gt;"
    )
    assert page.articles[0].images[1].path == "image"


def test_html_safe_text_skips_escape_when_no_special_chars():
    assert _html_safe_text("plain body") == "plain body"


def test_build_dom_uses_safe_relative_media_paths():
    dom = build_dom(
        [
            {"type": "image", "img_path": "images/page-1-photo.png"},
            {"type": "chart", "path": " charts/growth.png "},
            {"type": "image", "path": "../../etc/passwd"},
            {"type": "chart", "path": "/tmp/chart.png"},
            {"type": "image", "path": r"images\secret.png"},
            {"type": "chart", "path": "https://example.test/chart.png"},
            {"type": "image", "path": "images//bad.png"},
            {"type": "chart", "path": "./chart.png"},
            {"type": "image", "path": "x" * (MAX_MEDIA_PATH_LENGTH + 1)},
            {"type": "chart", "path": "charts/bad name.png"},
            {"type": "image", "path": "images/bad`name.png"},
            {"type": "chart", "path": "charts/bad<name>.png"},
            {"type": "image", "path": "images/bad'name.png"},
            {"type": "chart", "path": 123},
            {"type": "image", "path": "   "},
            {"type": "chart"},
        ],
        document_id="doc-safe-media-paths",
    )

    assert [image.path for image in dom.pages[0].articles[0].images] == [
        "images/page-1-photo.png",
        "charts/growth.png",
        "image",
        "chart",
        "image",
        "chart",
        "image",
        "chart",
        "image",
        "chart",
        "image",
        "chart",
        "image",
        "chart",
        "image",
        "chart",
    ]


def test_build_dom_creates_table_article_when_needed():
    dom = build_dom(
        [{"type": "table", "table_body": "<table></table>", "bbox": [1, 1, 2, 2]}],
        document_id="doc3",
    )
    assert dom.pages[0].articles[0].headline == "(table-block)"
    assert dom.pages[0].articles[0].body_blocks == ["&lt;table&gt;&lt;/table&gt;"]


def test_build_dom_skips_empty_table_body():
    dom = build_dom(
        [{"type": "table", "table_body": "   ", "bbox": [1, 1, 2, 2]}],
        document_id="doc-empty-table",
    )
    assert dom.pages[0].articles[0].headline == "(table-block)"
    assert dom.pages[0].articles[0].body_blocks == []


def test_build_dom_creates_untitled_article_for_plain_text():
    dom = build_dom(
        [{"type": "text", "text": "plain body", "bbox": [1, 1, 2, 2]}],
        document_id="doc4",
    )
    assert dom.pages[0].articles[0].headline == "(untitled)"


def test_build_dom_preserves_multi_page_structure_and_page_scoped_metadata():
    sample = _load_fixture("mineru_multi_page_sample.json")
    model = _load_fixture("mineru_multi_page_model.json")
    dom = build_dom(sample, document_id="doc-multi-page", model=model)

    assert len(dom.pages) == 2

    first_page = dom.pages[0]
    second_page = dom.pages[1]

    assert [page.page_number for page in dom.pages] == [1, 2]
    assert (first_page.width, first_page.height) == (1200.0, 1800.0)
    assert (second_page.width, second_page.height) == (1280.0, 1820.0)
    assert first_page.headers == ["Synthetic News Page 1"]
    assert second_page.headers == ["Synthetic News Page 2"]
    assert first_page.footers == ["Page 1 footer"]
    assert second_page.footers == ["Page 2 footer"]
    assert first_page.page_numbers == ["1"]
    assert second_page.page_numbers == ["2"]

    first_article = first_page.articles[0]
    second_article = second_page.articles[0]

    assert "Page 1 footer" not in first_article.body_blocks
    assert "Page 2 footer" not in second_article.body_blocks
    assert "1" not in first_article.body_blocks
    assert "2" not in second_article.body_blocks

    assert first_article.images[0].path == "images/page-1-photo.png"
    assert first_article.images[0].media_type == "image"
    assert [caption.text for caption in first_article.images[0].captions] == [
        "Image caption on page 1"
    ]
    assert [caption.text for caption in first_article.images[0].footnotes] == [
        "Image footnote on page 1"
    ]

    assert second_article.images[0].path == "charts/page-2-growth.png"
    assert second_article.images[0].media_type == "chart"
    assert [caption.text for caption in second_article.images[0].captions] == [
        "Chart caption on page 2"
    ]
    assert [caption.text for caption in second_article.images[0].footnotes] == [
        "Chart footnote on page 2"
    ]
    assert second_article.captions[0].text == "Table caption on page 2"
    assert second_article.footnotes[0].text == "Table footnote on page 2"
    assert any("page_idx" in warning for warning in dom.quality.warnings)


def test_coerce_page_number_returns_none_for_type_and_value_errors():
    assert _coerce_page_number(object()) is None
    assert _coerce_page_number("not-a-page-number") is None
    assert _coerce_page_number(None) is None
    assert _coerce_page_number(True) is None
    assert _coerce_page_number(False) is None
    assert _coerce_page_number(float("inf")) is None
    assert _coerce_page_number(0) is None
    assert _coerce_page_number(-1) is None
    assert _coerce_page_number(MAX_PAGE_NUMBER + 1) is None
    assert _coerce_page_number("7") == 7
    assert _coerce_page_number(MAX_PAGE_NUMBER) == MAX_PAGE_NUMBER


def test_caption_nodes_from_items_uses_contents_and_bbox_variants_and_skips_empty_text():
    nodes = _caption_nodes_from_items(
        [
            {"contents": " Caption from contents ", "bbox": [1, 2, 3, 4]},
            {"text": "   ", "bbox": [9, 9, 9, 9]},
            {"contents": "Caption from box", "box": [5, 6, 7, 8]},
            "Plain string caption",
            "   ",
        ]
    )

    assert [node.text for node in nodes] == [
        "Caption from contents",
        "Caption from box",
        "Plain string caption",
    ]
    assert nodes[2].bbox is None
    assert nodes[0].bbox is not None
    assert nodes[0].bbox.x0 == 1.0
    assert nodes[0].bbox.y1 == 4.0
    assert nodes[1].bbox is not None
    assert nodes[1].bbox.x0 == 5.0
    assert nodes[1].bbox.y1 == 8.0


def test_build_dom_preserves_multi_page_structure_from_page_idx_and_model():
    dom = build_dom(
        [
            {
                "type": "text",
                "text": "Front page headline",
                "text_level": 1,
                "bbox": [0, 0, 10, 10],
                "page_idx": 0,
            },
            {
                "type": "text",
                "text": "Front page body",
                "bbox": [0, 10, 10, 20],
                "page_idx": 0,
            },
            {
                "type": "text",
                "text": "Second page headline",
                "text_level": 1,
                "bbox": [0, 0, 10, 10],
                "page_idx": 1,
            },
            {
                "type": "text",
                "text": "Second page body",
                "bbox": [0, 10, 10, 20],
                "page_idx": 1,
            },
        ],
        document_id="doc-multi",
        model=[
            {"page_info": {"page_no": 0, "width": 100.0, "height": 200.0}},
            {"page_info": {"page_no": 1, "width": 110.0, "height": 210.0}},
        ],
    )

    assert [page.page_number for page in dom.pages] == [1, 2]
    assert dom.pages[0].width == 100.0
    assert dom.pages[0].height == 200.0
    assert dom.pages[1].width == 110.0
    assert dom.pages[1].height == 210.0
    assert dom.pages[0].articles[0].headline == "Front page headline"
    assert dom.pages[0].articles[0].body_blocks == ["Front page body"]
    assert dom.pages[1].articles[0].headline == "Second page headline"
    assert dom.pages[1].articles[0].body_blocks == ["Second page body"]


def test_build_dom_does_not_emit_page_divergence_warning_without_model():
    dom = build_dom(
        [
            {
                "type": "text",
                "text": "Body only",
                "bbox": [1, 1, 2, 2],
                "page_idx": 1,
            }
        ],
        document_id="doc5",
        model=None,
    )

    assert [page.page_number for page in dom.pages] == [2]
    assert dom.quality.warnings == []


def test_build_dom_prefers_model_page_number_when_it_differs_from_page_idx():
    dom = build_dom(
        [
            {
                "type": "text",
                "text": "Shifted page",
                "text_level": 1,
                "bbox": [0, 0, 10, 10],
                "page_idx": 0,
            }
        ],
        document_id="doc6",
        model=[{"page_info": {"page_no": 4, "width": 90.0, "height": 190.0}}],
    )

    assert [page.page_number for page in dom.pages] == [5]
    assert dom.pages[0].width == 90.0
    assert dom.pages[0].height == 190.0


def test_build_dom_prefers_explicit_model_page_number_field():
    dom = build_dom(
        [
            {
                "type": "text",
                "text": "Shifted page",
                "text_level": 1,
                "bbox": [0, 0, 10, 10],
                "page_idx": 0,
            }
        ],
        document_id="doc6b",
        model=[{"page_info": {"page_number": 9, "width": 90.0, "height": 190.0}}],
    )

    assert [page.page_number for page in dom.pages] == [9]


def test_build_dom_uses_model_page_metadata_when_page_idx_is_absent():
    dom = build_dom(
        [{"type": "text", "text": "headline", "text_level": 1, "bbox": [0, 0, 1, 1]}],
        document_id="doc7",
        model=[{"page_info": {"page_no": 4, "width": 90.0, "height": 190.0}}],
    )

    assert [page.page_number for page in dom.pages] == [5]
    assert dom.pages[0].width == 90.0
    assert dom.pages[0].height == 190.0


def test_build_dom_preserves_model_page_count_when_page_idx_is_absent_for_multipage_model():
    dom = build_dom(
        [{"type": "text", "text": "headline", "text_level": 1, "bbox": [0, 0, 1, 1]}],
        document_id="doc7b",
        model=[
            {"page_info": {"page_no": 4, "width": 90.0, "height": 190.0}},
            {"page_info": {"page_no": 5, "width": 91.0, "height": 191.0}},
        ],
    )

    assert [page.page_number for page in dom.pages] == [5, 6]
    assert dom.pages[0].articles[0].headline == "headline"
    assert dom.pages[1].articles == []
    assert dom.pages[1].width == 91.0
    assert dom.pages[1].height == 191.0
    assert any("page_idx" in warning for warning in dom.quality.warnings)


def test_build_dom_warns_when_blocks_are_missing_page_idx_in_multi_page_mode():
    dom = build_dom(
        [
            {
                "type": "text",
                "text": "page-two-headline",
                "text_level": 1,
                "bbox": [0, 0, 1, 1],
                "page_idx": 1,
            },
            {"type": "text", "text": "untagged-body", "bbox": [0, 1, 1, 2]},
        ],
        document_id="doc8",
        model=[
            {"page_info": {"page_no": 0, "width": 10.0, "height": 10.0}},
            {"page_info": {"page_no": 1, "width": 20.0, "height": 20.0}},
        ],
    )

    assert [page.page_number for page in dom.pages] == [1, 2]
    assert any("page_idx" in warning for warning in dom.quality.warnings)


def test_build_dom_keeps_article_ids_unique_across_pages():
    dom = build_dom(
        [
            {
                "type": "text",
                "text": "Page one",
                "text_level": 1,
                "bbox": [0, 0, 1, 1],
                "page_idx": 0,
            },
            {
                "type": "text",
                "text": "Page two",
                "text_level": 1,
                "bbox": [0, 0, 1, 1],
                "page_idx": 1,
            },
        ],
        document_id="doc9",
        model=[
            {"page_info": {"page_no": 0}},
            {"page_info": {"page_no": 1}},
        ],
    )

    article_ids = [
        article.article_id for page in dom.pages for article in page.articles
    ]
    assert article_ids == ["article-1", "article-2"]


def test_page_number_from_info():
    # Test valid page_number
    assert _page_number_from_info({"page_number": 5}, fallback=1) == 5

    # Test valid page_no (0-indexed, so 5 means page 6)
    assert _page_number_from_info({"page_no": 5}, fallback=1) == 6

    # Test precedence: page_number should win
    assert _page_number_from_info({"page_number": 5, "page_no": 10}, fallback=1) == 5

    # Test invalid values (not int)
    assert _page_number_from_info({"page_number": "5"}, fallback=1) == 1
    assert _page_number_from_info({"page_number": "5", "page_no": 4}, fallback=1) == 5
    assert _page_number_from_info({"page_no": "5"}, fallback=1) == 1
    assert _page_number_from_info({"page_number": None}, fallback=1) == 1
    assert _page_number_from_info({"page_number": -1, "page_no": 0}, fallback=9) == 1
    assert _page_number_from_info({"page_number": True, "page_no": 0}, fallback=9) == 1
    assert _page_number_from_info({"page_number": MAX_PAGE_NUMBER + 1}, fallback=9) == 9
    assert _page_number_from_info({"page_no": -1}, fallback=9) == 9
    assert _page_number_from_info({"page_no": True}, fallback=9) == 9
    assert _page_number_from_info({"page_no": MAX_PAGE_NUMBER}, fallback=9) == 9

    # Test missing keys
    assert _page_number_from_info({}, fallback=1) == 1


def test_bbox_helper_returns_bbox_for_valid_values():
    bbox = _bbox_from_values([1.1, 2.2, 3.3, 4.4])
    assert bbox is not None
    assert bbox.x0 == 1.1
    assert bbox.y0 == 2.2
    assert bbox.x1 == 3.3
    assert bbox.y1 == 4.4


def test_bbox_helper_handles_int_values():
    bbox = _bbox_from_values([1, 2, 3, 4])
    assert bbox is not None
    assert bbox.x0 == 1.0
    assert bbox.y0 == 2.0
    assert bbox.x1 == 3.0
    assert bbox.y1 == 4.0


def test_bbox_helper_returns_none_for_empty_list():
    assert _bbox_from_values([]) is None


def test_bbox_helper_returns_none_for_too_many_values():
    assert _bbox_from_values([1.0, 2.0, 3.0, 4.0, 5.0]) is None


def test_new_article_creates_deterministic_ids_with_fields():
    from itertools import count
    from newsdom_api.schemas import BoundingBox

    seq = count(1)

    # Test without bbox
    article1 = _new_article(seq, "First Headline")
    assert article1.article_id == "article-1"
    assert article1.headline == "First Headline"
    assert article1.bbox is None

    # Test with bbox
    bbox = BoundingBox(x0=0.0, y0=0.0, x1=100.0, y1=100.0)
    article2 = _new_article(seq, "Second Headline", bbox)
    assert article2.article_id == "article-2"
    assert article2.headline == "Second Headline"
    assert article2.bbox == bbox


def test_bbox_helper_returns_none_for_invalid_y0_x1_y1():
    assert _bbox_from_values([0, "bad", 1, 1]) is None
    assert _bbox_from_values([0, 0, "bad", 1]) is None
    assert _bbox_from_values([0, 0, 1, "bad"]) is None

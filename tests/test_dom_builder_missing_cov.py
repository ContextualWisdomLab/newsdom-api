from itertools import count

from newsdom_api.dom_builder import _build_page_dom


def test_missing_branches():
    content_list = [
        {"type": "text", "role": "header", "text": "   "},
        {"type": "text", "role": "footer", "text": "   "},
        {"type": "text", "role": "page_number", "text": "   "},
        {"type": "text", "role": "ad", "text": "   "},
    ]
    page = _build_page_dom(
        content_list,
        page_number=1,
        article_seq=count(1),
    )
    assert page.headers == []
    assert page.footers == []
    assert page.page_numbers == []
    assert page.ads == []

def test_unrolled_bbox_extraction():
    from newsdom_api.dom_builder import _bbox_from_values

    # Missing y0 coverage
    assert _bbox_from_values([0.0, None, 1.0, 1.0]) is None

    # Missing x1 coverage
    assert _bbox_from_values([0.0, 0.0, None, 1.0]) is None

    # Missing y1 coverage
    assert _bbox_from_values([0.0, 0.0, 1.0, None]) is None

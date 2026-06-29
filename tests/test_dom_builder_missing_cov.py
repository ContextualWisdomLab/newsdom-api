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

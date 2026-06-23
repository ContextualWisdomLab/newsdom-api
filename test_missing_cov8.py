import pytest
from newsdom_api.dom_builder import _build_page_dom
from itertools import count

def test_no_continue():
    content_list = [
        {"type": "text", "role": "UNKNOWN", "text": "UNKNOWN text"},
    ]
    page = _build_page_dom(
        content_list,
        page_number=1,
        article_seq=count(1),
    )
    assert page.articles[0].body_blocks == ["UNKNOWN text"]

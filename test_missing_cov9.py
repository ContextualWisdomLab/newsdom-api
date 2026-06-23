import pytest
from newsdom_api.dom_builder import _build_page_dom
from itertools import count

def test_missing_branches():
    content_list = [
        {"type": "text", "role": "header", "text": "   "},
        {"type": "text", "role": "footer", "text": "   "},
        {"type": "text", "role": "page_number", "text": "   "},
        {"type": "text", "role": "ad", "text": "   "},
        {"type": "text", "role": "header", "text": "header text"},
        {"type": "text", "role": "footer", "text": "footer text"},
        {"type": "text", "role": "page_number", "text": "page num"},
        {"type": "text", "role": "ad", "text": "ad text"},
        # We also need `if text is None` cache hit!
        {"type": "text", "role": "UNKNOWN", "text": "UNKNOWN"},
    ]
    page = _build_page_dom(
        content_list,
        page_number=1,
        article_seq=count(1),
    )

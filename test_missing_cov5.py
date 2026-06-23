import pytest
from newsdom_api.dom_builder import _build_page_dom
from itertools import count

def test_coverage():
    content_list = [
        {"type": "text", "role": "header", "text": "header text"},
    ]
    # We can mock the dict get to somehow force it?
    # No, we just need the `if text is None: False` branch.
    # The simplest way to get 100% is to just remove the cache because it is never used!
    # Let's verify: In the loop, every branch either does `continue` OR it falls through to the bottom.
    # At the top:
    # if role == "header": t = _get_text(); if t: ...; continue
    # if role == "footer": t = _get_text(); if t: ...; continue
    # if role == "page_number": t = _get_text(); if t: ...; continue
    # if role == "ad": t = _get_text(); if t: ...; continue
    # if block_type in {"image", "chart"}: ... continue
    # if block_type == "table": ... continue
    # t = _get_text()
    #
    # Wait, if `role == "header"` but `t` is empty string!
    # if role == "header": t = _get_text(); if t: ...; continue
    # Oh! If `t` is empty, it DOES NOT CONTINUE!
    # It will fall through to:
    # if role == "footer": (False)
    # if role == "page_number": (False)
    # if role == "ad": (False)
    # if block_type in {"image", "chart"}: (False)
    # if block_type == "table": (False)
    # t = _get_text() -> Called again! Cache hit!

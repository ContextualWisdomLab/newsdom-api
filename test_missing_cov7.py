import pytest
from newsdom_api.dom_builder import _build_page_dom
from itertools import count

def test_defer_text_coverage_double_call():
    # If the text is cached, we need to call _get_text() twice in the SAME block to cover `if text is None: False` branch.
    # The only way to call it twice is if it fails the first role check but we still call it.
    # Ah! But if we call it for `role == "header"`, it returns `t`. Then it continues!
    # Wait, if `t` is empty, it DOES NOT continue!
    # Let's verify:
    # if role == "header":
    #     t = _get_text()
    #     if t: page.headers.append(t)
    #     continue
    #
    # WAIT! It ALWAYS continues if `role == "header"`!
    #         if role == "header":
    #            t = _get_text()
    #            if t:
    #                page.headers.append(t)
    #            continue
    # YES! It ALWAYS continues.
    pass

import sys
import coverage

cov = coverage.Coverage(source=['newsdom_api.dom_builder'])
cov.start()
from newsdom_api.dom_builder import _coerce_page_number
_coerce_page_number(object())
_coerce_page_number("not-a-page-number")
_coerce_page_number(None)
_coerce_page_number(True)
_coerce_page_number(False)
_coerce_page_number([1, 2, 3])
_coerce_page_number({"a": 1})
_coerce_page_number(1)
_coerce_page_number("2")
cov.stop()
cov.save()
cov.report(show_missing=True, include='src/newsdom_api/dom_builder.py')

import sys
import coverage
import pytest
from tests.test_dom_builder import test_coerce_page_number_returns_none_for_type_and_value_errors

cov = coverage.Coverage(source=['newsdom_api.dom_builder'])
cov.start()
test_coerce_page_number_returns_none_for_type_and_value_errors()
cov.stop()
cov.save()
cov.report(show_missing=True, include='src/newsdom_api/dom_builder.py')

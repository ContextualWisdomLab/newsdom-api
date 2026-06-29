import coverage
import pytest

cov = coverage.Coverage(source=['src/newsdom_api/dom_builder.py'])
cov.start()
pytest.main(['tests/test_dom_builder.py', '-k', '_coerce_page_number'])
cov.stop()
cov.save()
cov.report(show_missing=True)

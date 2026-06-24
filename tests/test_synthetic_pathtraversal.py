import pytest
from pathlib import Path
from newsdom_api.synthetic import generate_fixture

def test_generate_fixture_path_traversal():
    with pytest.raises(ValueError, match="Path traversal detected"):
        generate_fixture(Path("../../etc"), seed=123)

from pathlib import Path

import pytest

from newsdom_api.synthetic import generate_fixture


def test_generate_fixture_rejects_relative_path_traversal() -> None:
    with pytest.raises(ValueError, match="Path traversal detected"):
        generate_fixture(Path("../../etc"), seed=123)

from pathlib import Path
import tempfile
import shutil

import pytest

from newsdom_api.synthetic import generate_fixture


def test_generate_fixture_rejects_relative_path_traversal() -> None:
    with pytest.raises(ValueError, match="Path traversal detected"):
        generate_fixture(Path("../../etc"), seed=123)


def test_generate_fixture_rejects_absolute_path_traversal() -> None:
    with pytest.raises(ValueError, match="Path traversal detected"):
        generate_fixture(Path("/etc/passwd"), seed=123)


def test_generate_fixture_accepts_absolute_tempdir() -> None:
    temp_dir = Path(tempfile.gettempdir()).resolve() / "newsdom_test_dir"
    try:
        generate_fixture(temp_dir, seed=123)
        assert temp_dir.exists()
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

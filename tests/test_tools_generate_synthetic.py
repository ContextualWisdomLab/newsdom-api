from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from tools import generate_synthetic


@patch("tools.generate_synthetic.generate_fixture")
def test_generate_synthetic_success(mock_generate, tmp_path, capsys):
    mock_generate.return_value = (tmp_path / "1.pdf", tmp_path / "1.json")

    generate_synthetic.main([str(tmp_path), "--seed", "42", "--count", "2"])

    out = capsys.readouterr().out
    assert "Generating fixture with seed 42" in out
    assert "Generating fixture with seed 43" in out
    assert "All fixtures generated successfully." in out
    assert mock_generate.call_count == 2


@patch("tools.generate_synthetic.generate_fixture")
def test_generate_synthetic_create_dir(mock_generate, tmp_path):
    out_dir = tmp_path / "new_dir"
    mock_generate.return_value = (out_dir / "1.pdf", out_dir / "1.json")

    generate_synthetic.main([str(out_dir), "--count", "1"])

    assert out_dir.exists()
    assert out_dir.is_dir()
    mock_generate.assert_called_once()


def test_generate_synthetic_dir_is_file(tmp_path, capsys):
    file_path = tmp_path / "existing_file.txt"
    file_path.write_text("dummy")

    with pytest.raises(SystemExit) as e:
        generate_synthetic.main([str(file_path)])

    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "exists and is not a directory" in err


@patch("tools.generate_synthetic.generate_fixture")
def test_generate_synthetic_exception(mock_generate, tmp_path, capsys):
    mock_generate.side_effect = Exception("Mock generator error")

    with pytest.raises(SystemExit) as e:
        generate_synthetic.main([str(tmp_path)])

    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "Mock generator error" in err


def test_generate_synthetic_main_block():
    content = Path("tools/generate_synthetic.py").read_text()
    assert 'if __name__ == "__main__":' in content
    assert "main()" in content.split('if __name__ == "__main__":')[1]

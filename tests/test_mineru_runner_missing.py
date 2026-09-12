import pytest
from pathlib import Path
from newsdom_api.mineru_runner import _find_output_dir

def test_find_output_dir_oserror(monkeypatch, tmp_path: Path):
    def fake_iterdir(self):
        raise OSError("Permission denied")
    monkeypatch.setattr(Path, "iterdir", fake_iterdir)
    with pytest.raises(FileNotFoundError):
        _find_output_dir(tmp_path)

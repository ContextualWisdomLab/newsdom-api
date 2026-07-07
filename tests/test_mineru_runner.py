from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from newsdom_api.errors import MineruRuntimeUnavailableError
from newsdom_api.mineru_runner import build_mineru_command, run_mineru


def test_build_mineru_command_uses_pipeline_backend(tmp_path: Path):
    cmd = build_mineru_command(Path("input.pdf"), tmp_path)
    assert "pipeline" in cmd
    assert "ocr" in cmd
    assert "japan" in cmd


def test_run_mineru_handles_timeout(tmp_path: Path):
    """
    Given a PDF that causes the mineru subprocess to time out,
    run_mineru should raise an MineruRuntimeUnavailableError to prevent hanging.
    """
    input_pdf = tmp_path / "dummy.pdf"
    input_pdf.write_text("dummy content")

    with patch("subprocess.run") as mock_run, \
         patch("shutil.which", return_value="mineru"):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="mineru", timeout=0.1)

        with pytest.raises(MineruRuntimeUnavailableError) as exc_info:
            run_mineru(input_pdf)

        assert exc_info.value.returncode == -1
        assert "OCR processing timed out" in str(exc_info.value.stderr)


def test_run_mineru_handles_called_process_error(tmp_path: Path):
    """
    Given a PDF that causes a non-zero exit code,
    run_mineru should raise an MineruRuntimeUnavailableError with the stderr.
    """
    input_pdf = tmp_path / "dummy.pdf"
    input_pdf.write_text("dummy content")

    with patch("subprocess.run") as mock_run, \
         patch("shutil.which", return_value="mineru"):
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="mineru", stderr="Something went wrong"
        )

        with pytest.raises(MineruRuntimeUnavailableError) as exc_info:
            run_mineru(input_pdf)

        assert exc_info.value.returncode == 1
        assert "Something went wrong" in str(exc_info.value.stderr)

from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from newsdom_api.errors import MineruRuntimeUnavailableError
from newsdom_api.mineru_runner import (
    _find_output_dir,
    build_mineru_command,
    normalize_language,
    normalize_mode,
    run_mineru,
)


def test_build_mineru_command_defaults_to_language_agnostic_auto(tmp_path: Path):
    """Defaults must be language-agnostic: pipeline backend, mode auto, lang auto."""
    cmd = build_mineru_command(Path("input.pdf"), tmp_path)
    assert "pipeline" in cmd
    # -m/-l flags carry the auto defaults, not the legacy japan/ocr coupling.
    assert cmd[cmd.index("-m") + 1] == "auto"
    assert cmd[cmd.index("-l") + 1] == "auto"
    assert "japan" not in cmd


def test_build_mineru_command_honors_explicit_language_and_mode(tmp_path: Path):
    """Explicit language/mode (e.g. legacy japan/ocr) are threaded to the CLI."""
    cmd = build_mineru_command(
        Path("input.pdf"), tmp_path, language="japan", mode="ocr"
    )
    assert cmd[cmd.index("-m") + 1] == "ocr"
    assert cmd[cmd.index("-l") + 1] == "japan"


def test_build_mineru_command_lowercases_language_and_mode(tmp_path: Path):
    cmd = build_mineru_command(Path("input.pdf"), tmp_path, language="EN", mode="TXT")
    assert cmd[cmd.index("-m") + 1] == "txt"
    assert cmd[cmd.index("-l") + 1] == "en"


@pytest.mark.parametrize("bad_mode", ["", "pdf", "ocr;rm", "auto ocr"])
def test_build_mineru_command_rejects_invalid_mode(tmp_path: Path, bad_mode: str):
    with pytest.raises(ValueError, match="Unsupported MinerU mode"):
        build_mineru_command(Path("input.pdf"), tmp_path, mode=bad_mode)


@pytest.mark.parametrize("bad_language", ["", "en; rm -rf", "-l", "12", "ja zh"])
def test_build_mineru_command_rejects_invalid_language(
    tmp_path: Path, bad_language: str
):
    with pytest.raises(ValueError, match="Unsupported MinerU language"):
        build_mineru_command(Path("input.pdf"), tmp_path, language=bad_language)


def test_normalize_mode_and_language_pass_through_valid_values():
    assert normalize_mode(" Auto ") == "auto"
    assert normalize_language(" Japan ") == "japan"
    assert normalize_language("ch_server") == "ch_server"


def test_find_output_dir_prefers_requested_method(tmp_path: Path):
    (tmp_path / "doc" / "ocr").mkdir(parents=True)
    (tmp_path / "doc" / "txt").mkdir(parents=True)
    assert _find_output_dir(tmp_path, "txt").name == "txt"


def test_find_output_dir_falls_back_across_known_methods(tmp_path: Path):
    # Requested "auto" is absent; discovery falls back to the produced ocr dir.
    (tmp_path / "doc" / "ocr").mkdir(parents=True)
    assert _find_output_dir(tmp_path, "auto").name == "ocr"


def test_find_output_dir_raises_when_no_method_dir_exists(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        _find_output_dir(tmp_path, "auto")


def test_run_mineru_forwards_language_and_mode(tmp_path: Path):
    """run_mineru must pass the requested language/mode down to the CLI builder."""
    input_pdf = tmp_path / "dummy.pdf"
    input_pdf.write_text("dummy content")
    captured = {}

    def fake_build(input_pdf, output_dir, *, mineru_bin, language, mode):
        captured["language"] = language
        captured["mode"] = mode
        return ["mineru"]

    def fake_execute(cmd):
        class Result:
            stdout = "out"
            stderr = "err"

        return Result()

    def fake_parse(output_dir, pdf, method):
        captured["method"] = method
        return [], []

    with (
        patch("newsdom_api.mineru_runner._resolve_mineru_bin", return_value="mineru"),
        patch("newsdom_api.mineru_runner.build_mineru_command", fake_build),
        patch("newsdom_api.mineru_runner._execute_mineru", fake_execute),
        patch("newsdom_api.mineru_runner._parse_mineru_output", fake_parse),
    ):
        run_mineru(input_pdf, language="korean", mode="txt")

    assert captured["language"] == "korean"
    assert captured["mode"] == "txt"
    assert captured["method"] == "txt"


def test_run_mineru_handles_timeout(tmp_path: Path):
    """
    Given a PDF that causes the mineru subprocess to time out,
    run_mineru should raise an MineruRuntimeUnavailableError to prevent hanging.
    """
    input_pdf = tmp_path / "dummy.pdf"
    input_pdf.write_text("dummy content")

    with (
        patch("subprocess.run") as mock_run,
        patch("newsdom_api.mineru_runner._cached_which", return_value="mineru"),
    ):
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

    with (
        patch("subprocess.run") as mock_run,
        patch("newsdom_api.mineru_runner._cached_which", return_value="mineru"),
    ):
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="mineru", stderr="Something went wrong"
        )

        with pytest.raises(MineruRuntimeUnavailableError) as exc_info:
            run_mineru(input_pdf)

        assert exc_info.value.returncode == 1
        assert "Something went wrong" in str(exc_info.value.stderr)

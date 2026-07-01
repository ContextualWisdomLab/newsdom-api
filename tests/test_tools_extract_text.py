import json
import sys
import warnings
from pathlib import Path
from unittest.mock import patch
import runpy

import pytest

from tools.extract_text import extract_text, main


def get_sample_data():
    return {
        "pages": [
            {
                "articles": [
                    {
                        "headline": "First Headline",
                        "body_blocks": ["First paragraph.", "Second paragraph."],
                    },
                    {"headline": "", "body_blocks": ["Only body block."]},
                ]
            }
        ]
    }


def test_extract_text_stdout(tmp_path: Path, capsys):
    """Test extract_text without output path (prints to stdout)."""
    valid_json = tmp_path / "valid.json"
    valid_json.write_text(json.dumps(get_sample_data()), encoding="utf-8")

    extract_text(valid_json)
    captured = capsys.readouterr()
    assert "# First Headline" in captured.out
    assert "First paragraph." in captured.out
    assert "Second paragraph." in captured.out
    assert "Only body block." in captured.out
    assert "---" in captured.out


def test_extract_text_file(tmp_path: Path, capsys):
    """Test extract_text with output path."""
    valid_json = tmp_path / "valid.json"
    valid_json.write_text(json.dumps(get_sample_data()), encoding="utf-8")
    output_txt = tmp_path / "output.txt"

    extract_text(valid_json, output_path=output_txt)
    captured = capsys.readouterr()
    assert f"Extracted text saved to {output_txt}" in captured.out

    content = output_txt.read_text(encoding="utf-8")
    assert "# First Headline" in content
    assert "First paragraph." in content
    assert "Second paragraph." in content
    assert "Only body block." in content
    assert "---" in content


def test_extract_text_file_not_found(tmp_path: Path):
    """Test extract_text with non-existent file."""
    non_existent = tmp_path / "non_existent.json"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        extract_text(non_existent)


def test_extract_text_invalid_suffix(tmp_path: Path):
    """Test extract_text with non-json file."""
    invalid_suffix = tmp_path / "test.txt"
    invalid_suffix.write_text("test")
    with pytest.raises(ValueError, match="File must be a .json file."):
        extract_text(invalid_suffix)


def test_main_success_stdout(tmp_path: Path, capsys):
    """Test main function writing to stdout."""
    valid_json = tmp_path / "valid.json"
    valid_json.write_text(json.dumps(get_sample_data()), encoding="utf-8")

    main([str(valid_json)])
    captured = capsys.readouterr()
    assert "# First Headline" in captured.out


def test_main_success_file(tmp_path: Path, capsys):
    """Test main function writing to file."""
    valid_json = tmp_path / "valid.json"
    valid_json.write_text(json.dumps(get_sample_data()), encoding="utf-8")
    output_txt = tmp_path / "output.txt"

    main([str(valid_json), "--output", str(output_txt)])
    captured = capsys.readouterr()
    assert f"Extracted text saved to {output_txt}" in captured.out


def test_main_exception(tmp_path: Path, capsys):
    """Test main function exception handling."""
    invalid_suffix = tmp_path / "test.txt"
    invalid_suffix.write_text("test")

    with pytest.raises(SystemExit) as e:
        main([str(invalid_suffix)])
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error: File must be a .json file." in captured.err


def test_module_execution(tmp_path: Path):
    """Test __main__ block execution with a valid json."""
    valid_json = tmp_path / "valid.json"
    valid_json.write_text(json.dumps(get_sample_data()), encoding="utf-8")

    # Patch sys.argv to simulate running from command line
    with patch.object(sys, "argv", ["extract_text.py", str(valid_json)]):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            runpy.run_module("tools.extract_text", run_name="__main__")

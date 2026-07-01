import json
import sys
import warnings
from pathlib import Path
from unittest.mock import patch
import runpy

import pytest

from tools.validate_dom import validate_dom, main


def test_validate_dom_success(tmp_path: Path):
    """Test successful validation of a valid DOM JSON."""
    valid_json = tmp_path / "valid.json"
    valid_data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art_1",
                        "headline": "Test Headline",
                        "body_blocks": ["Test body."],
                    }
                ],
            }
        ],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }
    valid_json.write_text(json.dumps(valid_data), encoding="utf-8")

    assert validate_dom(valid_json) is True


def test_validate_dom_json_decode_error(tmp_path: Path, capsys):
    """Test validation failure with malformed JSON."""
    malformed_json = tmp_path / "malformed.json"
    malformed_json.write_text("{invalid json", encoding="utf-8")

    assert validate_dom(malformed_json) is False
    captured = capsys.readouterr()
    assert "JSON Decode Error" in captured.err


def test_validate_dom_validation_error(tmp_path: Path, capsys):
    """Test validation failure with invalid DOM JSON."""
    invalid_json = tmp_path / "invalid.json"
    # Missing required field 'document_id'
    invalid_data = {"pages": []}
    invalid_json.write_text(json.dumps(invalid_data), encoding="utf-8")

    assert validate_dom(invalid_json) is False
    captured = capsys.readouterr()
    assert "Validation Error" in captured.err


def test_validate_dom_file_not_found(tmp_path: Path):
    """Test validate_dom with a non-existent file."""
    non_existent = tmp_path / "non_existent.json"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        validate_dom(non_existent)


def test_validate_dom_invalid_suffix(tmp_path: Path):
    """Test validate_dom with a non-json file."""
    invalid_suffix = tmp_path / "test.txt"
    invalid_suffix.write_text("test")
    with pytest.raises(ValueError, match="File must be a .json file."):
        validate_dom(invalid_suffix)


def test_main_success(tmp_path: Path, capsys):
    """Test main function with successful validation."""
    valid_json = tmp_path / "valid.json"
    valid_data = {"document_id": "test_doc", "pages": []}
    valid_json.write_text(json.dumps(valid_data), encoding="utf-8")

    main([str(valid_json)])
    captured = capsys.readouterr()
    assert "Successfully validated valid.json" in captured.out


def test_main_validation_error(tmp_path: Path):
    """Test main function with validation error (exits with 1)."""
    invalid_json = tmp_path / "invalid.json"
    invalid_data = {}
    invalid_json.write_text(json.dumps(invalid_data), encoding="utf-8")

    with pytest.raises(SystemExit) as e:
        main([str(invalid_json)])
    assert e.value.code == 1


def test_main_exception(tmp_path: Path, capsys):
    """Test main function with other exceptions (exits with 1)."""
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
    valid_data = {"document_id": "test_doc", "pages": []}
    valid_json.write_text(json.dumps(valid_data), encoding="utf-8")

    # Patch sys.argv to simulate running from command line
    with patch.object(sys, "argv", ["validate_dom.py", str(valid_json)]):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            # Remove src dir from sys.path to hit the pragma: no cover path logic if needed,
            # but since we are testing tools/validate_dom.py directly we just run it.
            # actually we don't strictly need to remove it, run_module will work
            runpy.run_module("tools.validate_dom", run_name="__main__")

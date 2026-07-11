from __future__ import annotations
import runpy
import sys

import json
from pathlib import Path
import pytest

from pydantic import ValidationError
from tools.validate_dom import main, validate_dom


def test_validate_dom_success(tmp_path: Path) -> None:
    json_path = tmp_path / "valid.json"
    valid_data = {
        "document_id": "test-doc-123",
        "pages": [],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }
    json_path.write_text(json.dumps(valid_data), encoding="utf-8")

    validate_dom(json_path)


def test_validate_dom_file_not_found(tmp_path: Path) -> None:
    non_existent = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        validate_dom(non_existent)


def test_validate_dom_invalid_extension(tmp_path: Path) -> None:
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="File must be a .json file"):
        validate_dom(txt_path)


def test_validate_dom_invalid_json(tmp_path: Path) -> None:
    json_path = tmp_path / "invalid_json.json"
    json_path.write_text("invalid{json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        validate_dom(json_path)


def test_validate_dom_validation_error(tmp_path: Path) -> None:
    json_path = tmp_path / "invalid_schema.json"
    invalid_data = {
        # missing document_id
        "pages": []
    }
    json_path.write_text(json.dumps(invalid_data), encoding="utf-8")

    with pytest.raises(ValidationError):
        validate_dom(json_path)


def test_main_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    json_path = tmp_path / "valid.json"
    valid_data = {
        "document_id": "test-doc-123",
        "pages": [],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }
    json_path.write_text(json.dumps(valid_data), encoding="utf-8")

    main([str(json_path)])

    captured = capsys.readouterr()
    assert "Validation successful: JSON matches ParseResponse schema." in captured.out


def test_main_validation_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    json_path = tmp_path / "invalid_schema.json"
    invalid_data = {"pages": []}
    json_path.write_text(json.dumps(invalid_data), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main([str(json_path)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Validation Error" in captured.err


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    non_existent = tmp_path / "missing.json"

    with pytest.raises(SystemExit) as exc_info:
        main([str(non_existent)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "File not found" in captured.err


def test_sys_path_injection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Clear sys.path to force the injection block to run
    monkeypatch.setattr(sys, "path", [])

    json_path = tmp_path / "valid.json"
    valid_data = {
        "document_id": "test-doc-123",
        "pages": [],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }
    json_path.write_text(json.dumps(valid_data), encoding="utf-8")

    # Mock sys.argv
    monkeypatch.setattr(sys, "argv", ["validate_dom.py", str(json_path)])

    # Run the module to cover the import condition and __main__ block
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        runpy.run_module("tools.validate_dom", run_name="__main__")

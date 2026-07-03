from __future__ import annotations

import json
from pathlib import Path
import pytest
import runpy
import sys
import warnings

from tools import validate_dom


@pytest.fixture
def mock_valid_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "valid.json"
    data = {
        "document_id": "doc_123",
        "pages": [],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


@pytest.fixture
def mock_invalid_schema_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "invalid_schema.json"
    # Missing document_id which is required in ParseResponse
    data = {"pages": []}
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


@pytest.fixture
def mock_invalid_format_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "invalid_format.json"
    json_path.write_text("{ this is not a valid json ", encoding="utf-8")
    return json_path


def test_validate_dom_success(mock_valid_json_file, capsys):
    validate_dom.main([str(mock_valid_json_file)])
    out = capsys.readouterr().out
    assert "Validation successful" in out


def test_validate_dom_invalid_schema(mock_invalid_schema_json_file, capsys):
    with pytest.raises(SystemExit) as e:
        validate_dom.main([str(mock_invalid_schema_json_file)])
    assert e.value.code == 1
    assert "Schema validation failed" in capsys.readouterr().err


def test_validate_dom_invalid_format(mock_invalid_format_json_file, capsys):
    with pytest.raises(SystemExit) as e:
        validate_dom.main([str(mock_invalid_format_json_file)])
    assert e.value.code == 1
    assert "Invalid JSON format" in capsys.readouterr().err


def test_validate_dom_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        validate_dom.main([str(tmp_path / "missing.json")])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err


def test_validate_dom_wrong_ext(tmp_path, capsys):
    txt = tmp_path / "wrong.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        validate_dom.main([str(txt)])
    assert e.value.code == 1
    assert "must be a .json file" in capsys.readouterr().err


def test_validate_dom_main_execution(monkeypatch, mock_valid_json_file):
    monkeypatch.setattr(sys, "argv", ["validate_dom.py", str(mock_valid_json_file)])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        runpy.run_module("tools.validate_dom", run_name="__main__")


def test_validate_dom_help_exit(capsys):
    with pytest.raises(SystemExit) as e:
        validate_dom.main(["--help"])
    assert e.value.code == 0
    assert "Validate a NewsDOM JSON output" in capsys.readouterr().out


def test_validate_dom_interrupt(monkeypatch, mock_valid_json_file):
    def mock_validate(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(validate_dom, "validate_dom", mock_validate)

    with pytest.raises(SystemExit) as e:
        validate_dom.main([str(mock_valid_json_file)])
    assert e.value.code == 130

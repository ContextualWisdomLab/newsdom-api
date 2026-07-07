from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from tools import validate_dom


@pytest.fixture
def valid_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "valid.json"
    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art_1",
                        "headline": "Test Headline",
                        "body_blocks": ["This is the body."],
                    }
                ],
            }
        ],
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


@pytest.fixture
def invalid_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "invalid.json"
    data = {"pages": [{"page_number": "not_an_int"}]}
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_validate_json_file_success(valid_json_file):
    assert validate_dom.validate_json_file(valid_json_file) is True


def test_validate_json_file_not_found(tmp_path, capsys):
    assert validate_dom.validate_json_file(tmp_path / "missing.json") is False
    assert "File not found" in capsys.readouterr().err


def test_validate_json_file_wrong_ext(tmp_path, capsys):
    txt = tmp_path / "wrong.txt"
    txt.write_text("{}", encoding="utf-8")
    assert validate_dom.validate_json_file(txt) is False
    assert "must be a .json file" in capsys.readouterr().err


def test_validate_json_file_malformed(tmp_path, capsys):
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{bad json", encoding="utf-8")
    assert validate_dom.validate_json_file(malformed) is False
    assert "Invalid JSON format" in capsys.readouterr().err


def test_validate_json_file_oserror(tmp_path, monkeypatch, capsys):
    file_path = tmp_path / "oserror.json"
    file_path.write_text("{}", encoding="utf-8")

    def mock_read_text(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "read_text", mock_read_text)
    assert validate_dom.validate_json_file(file_path) is False
    assert "Could not read" in capsys.readouterr().err


def test_validate_json_file_validation_error(invalid_json_file, capsys):
    assert validate_dom.validate_json_file(invalid_json_file) is False
    assert "Validation failed for" in capsys.readouterr().err


def test_main_success_file(valid_json_file, capsys):
    validate_dom.main([str(valid_json_file)])
    assert "Validation successful:" in capsys.readouterr().out


def test_main_failure_file(invalid_json_file):
    with pytest.raises(SystemExit) as e:
        validate_dom.main([str(invalid_json_file)])
    assert e.value.code == 1


def test_main_dir_recursive(tmp_path, valid_json_file, capsys):
    sub = tmp_path / "sub"
    sub.mkdir()
    valid2 = sub / "valid2.json"
    valid2.write_text(valid_json_file.read_text(encoding="utf-8"), encoding="utf-8")

    validate_dom.main([str(tmp_path), "--recursive"])
    out = capsys.readouterr().out
    assert "valid.json" in out
    assert "valid2.json" in out


def test_main_dir_non_recursive(tmp_path, valid_json_file, capsys):
    sub = tmp_path / "sub"
    sub.mkdir()
    valid2 = sub / "valid2.json"
    valid2.write_text(valid_json_file.read_text(encoding="utf-8"), encoding="utf-8")

    validate_dom.main([str(tmp_path)])
    out = capsys.readouterr().out
    assert "valid.json" in out
    assert "valid2.json" not in out


def test_main_input_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        validate_dom.main([str(tmp_path / "missing")])
    assert e.value.code == 1
    assert "Input path not found" in capsys.readouterr().err


def test_main_no_json_files(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        validate_dom.main([str(tmp_path)])
    assert e.value.code == 1
    assert "No JSON files found to validate" in capsys.readouterr().err


def test_sys_path_injection_branch(tmp_path, monkeypatch):
    """Test the branch where _SRC_ROOT is already in sys.path"""
    _REPO_ROOT = Path(validate_dom.__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"
    if str(_SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(_SRC_ROOT))

    file_path = tmp_path / "sys_path.json"
    file_path.write_text('{"document_id": "sys"}', encoding="utf-8")

    # Validation will fail but it will cover the path checking branch
    validate_dom.validate_json_file(file_path)


def test_sys_path_injection_bypass(tmp_path, monkeypatch):
    """Test the branch where _SRC_ROOT is NOT already in sys.path"""
    import sys

    # We must mock sys.path so the condition triggers
    _REPO_ROOT = Path(validate_dom.__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"

    mock_sys_path = []
    monkeypatch.setattr(sys, "path", mock_sys_path)

    file_path = tmp_path / "sys_path_missing.json"
    file_path.write_text('{"document_id": "sys"}', encoding="utf-8")

    # Validation will fail but cover the insertion block
    validate_dom.validate_json_file(file_path)
    assert str(_SRC_ROOT) in mock_sys_path

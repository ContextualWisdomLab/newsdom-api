import json
import sys
import runpy
from pathlib import Path

import pytest
from pydantic import ValidationError

from tools.validate_dom import validate_dom, main


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "valid.json"
    data = {
        "document_id": "test_doc",
        "pages": [],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


@pytest.fixture
def mock_invalid_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "invalid.json"
    data = {
        "pages": [],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_validate_dom_success(mock_json_file: Path, capsys: pytest.CaptureFixture[str]):
    validate_dom(mock_json_file)


def test_validate_dom_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        validate_dom(tmp_path / "nonexistent.json")


def test_validate_dom_wrong_ext(tmp_path: Path):
    txt = tmp_path / "test.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_dom(txt)


def test_validate_dom_invalid_json_schema(mock_invalid_json_file: Path):
    with pytest.raises(ValidationError):
        validate_dom(mock_invalid_json_file)


def test_main_success(mock_json_file: Path, capsys: pytest.CaptureFixture[str]):
    main([str(mock_json_file)])
    captured = capsys.readouterr()
    assert "Validation successful" in captured.out


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as e:
        main([str(tmp_path / "nonexistent.json")])
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_validate_dom_sys_path_insertion(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "path", [])
    script_path = str(Path(__file__).resolve().parents[1] / "tools" / "validate_dom.py")
    runpy.run_path(script_path)
    assert len(sys.path) > 0

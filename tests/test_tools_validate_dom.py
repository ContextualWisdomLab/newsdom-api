from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tools.validate_dom import main, validate_dom


@pytest.fixture
def valid_json_data() -> dict:
    return {
        "document_id": "doc123",
        "pages": [],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }


def test_validate_dom_valid_json(
    tmp_path: Path, valid_json_data: dict, capsys: pytest.CaptureFixture
):
    json_path = tmp_path / "valid.json"
    json_path.write_text(json.dumps(valid_json_data), encoding="utf-8")

    validate_dom(json_path)  # Should not raise

    main([str(json_path)])
    assert "Validation successful: valid.json" in capsys.readouterr().out


def test_validate_dom_invalid_json(tmp_path: Path, capsys: pytest.CaptureFixture):
    json_path = tmp_path / "invalid.json"
    invalid_data = {"pages": []}  # Missing document_id
    json_path.write_text(json.dumps(invalid_data), encoding="utf-8")

    with pytest.raises(ValidationError):
        validate_dom(json_path)

    with pytest.raises(SystemExit) as e:
        main([str(json_path)])
    assert e.value.code == 1
    assert "Error: 1 validation error for ParseResponse" in capsys.readouterr().err


def test_validate_dom_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        validate_dom(missing_path)

    with pytest.raises(SystemExit) as e:
        main([str(missing_path)])
    assert e.value.code == 1
    assert "Error: File not found" in capsys.readouterr().err


def test_validate_dom_wrong_extension(
    tmp_path: Path, valid_json_data: dict, capsys: pytest.CaptureFixture
):
    txt_path = tmp_path / "wrong.txt"
    txt_path.write_text(json.dumps(valid_json_data), encoding="utf-8")

    with pytest.raises(ValueError, match="must be a .json file"):
        validate_dom(txt_path)

    with pytest.raises(SystemExit) as e:
        main([str(txt_path)])
    assert e.value.code == 1
    assert "Error: File must be a .json file" in capsys.readouterr().err


def test_validate_dom_malformed_json(tmp_path: Path, capsys: pytest.CaptureFixture):
    json_path = tmp_path / "malformed.json"
    json_path.write_text("invalid { json [", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        validate_dom(json_path)

    with pytest.raises(SystemExit) as e:
        main([str(json_path)])
    assert e.value.code == 1
    assert "Error: Expecting value:" in capsys.readouterr().err

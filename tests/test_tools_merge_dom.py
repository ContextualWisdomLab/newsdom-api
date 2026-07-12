from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.merge_dom import main, merge_dom

VALID_JSON_1 = {
    "document_id": "doc_1",
    "pages": [
        {
            "page_number": 1,
            "articles": [],
            "ads": [],
            "headers": [],
            "footers": [],
            "page_numbers": [],
        }
    ],
    "quality": {
        "status": "success",
        "parser": "mineru",
        "warnings": [],
    },
}

VALID_JSON_2 = {
    "document_id": "doc_1",
    "pages": [
        {
            "page_number": 2,
            "articles": [],
            "ads": [],
            "headers": [],
            "footers": [],
            "page_numbers": [],
        }
    ],
    "quality": {
        "status": "partial_success",
        "parser": "mineru",
        "warnings": ["Warning 1"],
    },
}


def test_merge_dom_success(tmp_path: Path) -> None:
    input1 = tmp_path / "1.json"
    input1.write_text(json.dumps(VALID_JSON_1), encoding="utf-8")
    input2 = tmp_path / "2.json"
    input2.write_text(json.dumps(VALID_JSON_2), encoding="utf-8")
    output = tmp_path / "merged.json"

    merge_dom([input1, input2], output)

    assert output.exists()
    merged_data = json.loads(output.read_text(encoding="utf-8"))

    assert merged_data["document_id"] == "doc_1"
    assert len(merged_data["pages"]) == 2
    assert merged_data["pages"][0]["page_number"] == 1
    assert merged_data["pages"][1]["page_number"] == 2
    assert merged_data["quality"]["status"] == "partial_success"
    assert "Warning 1" in merged_data["quality"]["warnings"]


def test_merge_dom_empty_inputs(tmp_path: Path) -> None:
    output = tmp_path / "merged.json"
    with pytest.raises(ValueError, match="No input files provided"):
        merge_dom([], output)


def test_merge_dom_invalid_file(tmp_path: Path) -> None:
    output = tmp_path / "merged.json"

    non_existent = tmp_path / "not_exist.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        merge_dom([non_existent], output)

    not_json = tmp_path / "input.txt"
    not_json.write_text("plain text", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a .json file"):
        merge_dom([not_json], output)

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{invalid_json:", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        merge_dom([invalid_json], output)

    invalid_schema = tmp_path / "schema.json"
    invalid_schema.write_text('{"document_id": 123}', encoding="utf-8")
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        merge_dom([invalid_schema], output)


def test_merge_dom_cli_success(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    input1 = tmp_path / "1.json"
    input1.write_text(json.dumps(VALID_JSON_1), encoding="utf-8")
    output = tmp_path / "merged.json"

    main([str(input1), "-o", str(output)])

    assert output.exists()
    captured = capsys.readouterr()
    assert "Merged JSON successfully written" in captured.out


def test_merge_dom_cli_invalid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    not_json = tmp_path / "input.txt"
    not_json.write_text("plain text", encoding="utf-8")
    output = tmp_path / "merged.json"

    with pytest.raises(SystemExit) as exc_info:
        main([str(not_json), "-o", str(output)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error merging JSON files:" in captured.err


def test_merge_dom_sys_path(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    monkeypatch.setattr(sys, "path", [])

    # Reloading module to cover sys.path insertion
    import importlib
    import tools.merge_dom

    importlib.reload(tools.merge_dom)

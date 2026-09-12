from pathlib import Path
import json
import sys
from unittest.mock import patch

import pytest

from tools.filter_dom import main, filter_dom


def test_filter_dom_success(tmp_path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "ads": ["Ad 1"],
                "headers": ["Header 1"],
                "footers": ["Footer 1"],
                "articles": []
            },
            {
                "page_number": 2,
                "articles": []
            }
        ],
        "quality": {"status": "success", "parser": "mineru"}
    }
    input_file.write_text(json.dumps(data))

    filter_dom(
        input_file,
        output_file,
        remove_ads=True,
        remove_headers=True,
        remove_footers=True,
    )

    assert output_file.exists()
    out_data = json.loads(output_file.read_text())
    page = out_data["pages"][0]
    page2 = out_data["pages"][1]

    assert page["ads"] == []
    assert page["headers"] == []
    assert page["footers"] == []

    assert "ads" not in page2
    assert "headers" not in page2
    assert "footers" not in page2


def test_filter_dom_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="File not found"):
        filter_dom(tmp_path / "nonexistent.json", tmp_path / "out.json")


def test_filter_dom_invalid_extension(tmp_path):
    input_file = tmp_path / "input.txt"
    input_file.touch()
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        filter_dom(input_file, tmp_path / "out.json")


def test_filter_dom_invalid_json(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text("not json")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(input_file, tmp_path / "out.json")


def test_filter_dom_schema_validation_error(tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps({"invalid": "data"}))
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        filter_dom(input_file, tmp_path / "out.json")


def test_main_success(tmp_path, capsys):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "out.json"
    data = {
        "document_id": "test_doc",
        "pages": [
            {"page_number": 1, "ads": ["Ad 1"], "articles": []}
        ],
        "quality": {"status": "success"}
    }
    input_file.write_text(json.dumps(data))

    main([str(input_file), "-o", str(output_file), "--remove-ads"])
    captured = capsys.readouterr()
    assert "Filtered JSON successfully written" in captured.out


def test_main_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([str(tmp_path / "nonexistent.json"), "-o", str(tmp_path / "out.json")])
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error filtering JSON file: File not found" in captured.err


def test_sys_path_injection_filter(monkeypatch):
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    monkeypatch.setattr(sys, "path", [path for path in sys.path if path != src_path])
    import runpy

    sys.modules.pop("tools.filter_dom", None)

    with patch("sys.argv", ["tools/filter_dom.py", "-h"]):
        try:
            runpy.run_module("tools.filter_dom", run_name="__main__")
        except SystemExit:
            pass

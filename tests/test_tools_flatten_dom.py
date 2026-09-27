import json
import os
import pytest
from pathlib import Path
from tools.flatten_dom import flatten_dom, main


def test_flatten_dom_success(tmp_path: Path):
    input_data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "headline": "Article 1"
                    }
                ]
            },
            {
                "page_number": 2,
                "articles": [
                    {
                        "headline": "Article 2",
                        "document_id": "override_doc",
                        "page_number": 99
                    }
                ]
            }
        ]
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    flatten_dom(input_file, output_file)

    assert output_file.exists()
    flattened_data = json.loads(output_file.read_text(encoding="utf-8"))

    assert type(flattened_data) is list
    assert len(flattened_data) == 2

    assert flattened_data[0]["headline"] == "Article 1"
    assert flattened_data[0]["document_id"] == "test_doc"
    assert flattened_data[0]["page_number"] == 1

    assert flattened_data[1]["headline"] == "Article 2"
    assert flattened_data[1]["document_id"] == "override_doc"
    assert flattened_data[1]["page_number"] == 99


def test_flatten_dom_same_file_error(tmp_path: Path):
    input_file = tmp_path / "input.json"
    input_file.touch()

    with pytest.raises(ValueError, match="Input and output paths must not be the same file."):
        flatten_dom(input_file, input_file)


def test_flatten_dom_not_json(tmp_path: Path):
    input_file = tmp_path / "input.txt"
    input_file.touch()
    output_file = tmp_path / "output.json"

    with pytest.raises(ValueError, match=r"Input file must be a \.json file\."):
        flatten_dom(input_file, output_file)


def test_flatten_dom_not_found(tmp_path: Path):
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    with pytest.raises(FileNotFoundError):
        flatten_dom(input_file, output_file)


def test_flatten_dom_invalid_json(tmp_path: Path):
    input_file = tmp_path / "input.json"
    input_file.write_text("invalid json", encoding="utf-8")
    output_file = tmp_path / "output.json"

    with pytest.raises(ValueError, match="Invalid JSON file:"):
        flatten_dom(input_file, output_file)


def test_flatten_dom_not_dict_root(tmp_path: Path):
    input_file = tmp_path / "input.json"
    input_file.write_text("[]", encoding="utf-8")
    output_file = tmp_path / "output.json"

    with pytest.raises(ValueError, match="Root of JSON must be an object."):
        flatten_dom(input_file, output_file)


def test_flatten_dom_nan_constant_error(tmp_path: Path):
    input_file = tmp_path / "input.json"
    input_file.write_text('{"val": NaN}', encoding="utf-8")
    output_file = tmp_path / "output.json"

    with pytest.raises(ValueError, match="Strict JSON parsing rejected non-standard constant"):
        flatten_dom(input_file, output_file)


def test_main_success(tmp_path: Path, capsys):
    input_file = tmp_path / "input.json"
    input_file.write_text('{"document_id": "test", "pages": []}', encoding="utf-8")
    output_file = tmp_path / "output.json"

    main([str(input_file), str(output_file)])
    captured = capsys.readouterr()
    assert "Flattened JSON successfully written to" in captured.out


def test_main_error(tmp_path: Path, capsys):
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), str(output_file)])

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error flattening JSON" in captured.err


def test_flatten_dom_empty_and_invalid_types(tmp_path: Path):
    # Test handling of invalid types that should be safely ignored
    input_data = {
        "pages": [
            "not a dict",
            {
                "page_number": 2,
                "articles": "not a list"
            },
            {
                "page_number": 3,
                "articles": [
                    "not a dict",
                    {
                        "headline": "Valid article"
                    }
                ]
            }
        ]
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    flatten_dom(input_file, output_file)

    flattened_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(flattened_data) == 1
    assert flattened_data[0]["headline"] == "Valid article"


def test_flatten_dom_replace_error(tmp_path: Path, monkeypatch):
    input_file = tmp_path / "input.json"
    input_file.write_text('{"pages": []}', encoding="utf-8")
    output_file = tmp_path / "output.json"

    def mock_replace(*args, **kwargs):
        raise OSError("Mock replace error")

    monkeypatch.setattr(os, "replace", mock_replace)

    with pytest.raises(OSError, match="Mock replace error"):
        flatten_dom(input_file, output_file)

def test_flatten_dom_not_list_pages(tmp_path: Path):
    input_data = {"pages": "not a list"}
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    flatten_dom(input_file, output_file)

    flattened_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert flattened_data == []

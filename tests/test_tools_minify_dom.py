from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.minify_dom import main, minify_dom


@pytest.fixture
def sample_dom_json(tmp_path: Path) -> Path:
    """Create a temporary valid DOM JSON file with spaces."""
    data = {
        "document_id": "test_doc",
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
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }
    file_path = tmp_path / "sample.json"
    # Write with indentation to ensure there are whitespaces to minify
    file_path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    return file_path


def test_minify_dom_success(sample_dom_json: Path):
    """Test successful minification of DOM."""
    result = minify_dom(sample_dom_json)

    # Assert there are no spaces outside of values
    assert " " not in result.replace('"test_doc"', "test_doc").replace(
        '"success"', "success"
    ).replace('"mineru"', "mineru")

    # Assert it's valid JSON and matches original data logically
    assert json.loads(result)["document_id"] == "test_doc"


def test_minify_dom_with_output(tmp_path: Path, sample_dom_json: Path):
    """Test minification writing to an output file."""
    out_path = tmp_path / "minified.json"
    minify_dom(sample_dom_json, out_path)

    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert " " not in content.replace('"test_doc"', "test_doc").replace(
        '"success"', "success"
    ).replace('"mineru"', "mineru")


def test_minify_dom_file_not_found(tmp_path: Path):
    """Test error when input file does not exist."""
    not_exist = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        minify_dom(not_exist)


def test_minify_dom_invalid_extension(tmp_path: Path):
    """Test error when input file is not a .json file."""
    invalid_ext = tmp_path / "sample.txt"
    invalid_ext.touch()
    with pytest.raises(ValueError, match="must be a .json file"):
        minify_dom(invalid_ext)


def test_minify_dom_invalid_json(tmp_path: Path):
    """Test error when input file contains invalid JSON."""
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{bad json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        minify_dom(invalid_json)


def test_minify_dom_schema_validation_error(tmp_path: Path):
    """Test error when JSON doesn't match schema."""
    bad_schema = tmp_path / "schema.json"
    bad_schema.write_text(
        '{"pages": [{"page_number": "not_an_int"}]}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        minify_dom(bad_schema)


@patch("sys.stdout")
def test_main_cli_stdout(mock_stdout, sample_dom_json: Path):
    """Test CLI outputting to stdout."""
    main([str(sample_dom_json)])
    assert mock_stdout.write.called


def test_main_cli_file_output(tmp_path: Path, sample_dom_json: Path):
    """Test CLI outputting to a file."""
    out_path = tmp_path / "out" / "minified.json"
    main([str(sample_dom_json), "-o", str(out_path)])

    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["document_id"] == "test_doc"


@patch("sys.stderr")
def test_main_cli_error(mock_stderr, tmp_path: Path):
    """Test CLI handles exceptions gracefully."""
    not_exist = tmp_path / "missing.json"
    with pytest.raises(SystemExit) as exc:
        main([str(not_exist)])

    assert exc.value.code == 1
    assert mock_stderr.write.called


def test_sys_path_injection(monkeypatch):
    """Test that sys.path injection works when the path is missing."""
    import sys
    from importlib import reload
    import tools.minify_dom

    target_path = str(tools.minify_dom._SRC_ROOT)

    # Remove the path
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != target_path])

    # Reload the module to trigger the injection
    reload(tools.minify_dom)

    assert target_path in sys.path

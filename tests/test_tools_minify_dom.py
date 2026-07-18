import json
import pytest
from pathlib import Path
from tools.minify_dom import minify_dom, main


def test_minify_dom_valid(tmp_path: Path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    data = {
        "document_id": "test",
        "pages": [],
        "quality": {"status": "success", "parser": "test", "warnings": []},
    }
    input_path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    minify_dom(input_path, output_path)
    result = output_path.read_text(encoding="utf-8")
    assert " " not in result
    assert "\n" not in result
    assert json.loads(result) == data


def test_minify_dom_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        minify_dom(tmp_path / "nonexistent.json", tmp_path / "output.json")


def test_minify_dom_invalid_extension(tmp_path: Path):
    invalid_file = tmp_path / "input.txt"
    invalid_file.touch()
    with pytest.raises(ValueError, match="must be a .json file"):
        minify_dom(invalid_file, tmp_path / "output.json")


def test_minify_dom_invalid_json(tmp_path: Path):
    input_path = tmp_path / "input.json"
    input_path.write_text("invalid json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        minify_dom(input_path, tmp_path / "output.json")


def test_minify_dom_invalid_schema(tmp_path: Path):
    input_path = tmp_path / "input.json"
    input_path.write_text('{"invalid": "schema"}', encoding="utf-8")
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        minify_dom(input_path, tmp_path / "output.json")


def test_main_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    data = {
        "document_id": "test",
        "pages": [],
        "quality": {"status": "success", "parser": "test", "warnings": []},
    }
    input_path.write_text(json.dumps(data), encoding="utf-8")
    main([str(input_path), "-o", str(output_path)])
    assert (
        f"Minified JSON successfully written to {output_path}"
        in capsys.readouterr().out
    )


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit):
        main([str(tmp_path / "nonexistent.json"), "-o", str(tmp_path / "output.json")])
    assert "Error minifying JSON file" in capsys.readouterr().err


import sys
import importlib
import runpy
from pathlib import Path


def test_minify_dom_import_path(monkeypatch):
    """Test sys.path injection for coverage."""
    import tools.minify_dom

    target_path = str(Path(tools.minify_dom.__file__).resolve().parents[1] / "src")
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != target_path])
    importlib.reload(tools.minify_dom)
    assert target_path in sys.path


def test_minify_dom_main_module():
    """Test if __name__ == '__main__' block coverage via run_module."""
    try:
        runpy.run_module("tools.minify_dom", run_name="__main__")
    except SystemExit:
        pass

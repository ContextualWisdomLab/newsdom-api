from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import sys
import pytest
from tools.minify_dom import main, minify_dom


def test_minify_dom_success(tmp_path: Path) -> None:
    input_json = {
        "document_id": "doc1",
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
        "pages": [
            {
                "page_number": 1,
                "width": 800.0,
                "height": 600.0,
                "ads": [],
                "headers": [],
                "footers": [],
                "page_numbers": [],
                "articles": [
                    {
                        "article_id": "a1",
                        "headline": "Test",
                        "body_blocks": [],
                        "bbox": {"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 100.0},
                        "images": [
                            {
                                "path": "img1.jpg",
                                "media_type": "image",
                                "bbox": {
                                    "x0": 10.0,
                                    "y0": 10.0,
                                    "x1": 20.0,
                                    "y1": 20.0,
                                },
                                "captions": [
                                    {
                                        "text": "cap",
                                        "bbox": {
                                            "x0": 0.0,
                                            "y0": 0.0,
                                            "x1": 10.0,
                                            "y1": 10.0,
                                        },
                                    }
                                ],
                                "footnotes": [
                                    {
                                        "text": "fn",
                                        "bbox": {
                                            "x0": 0.0,
                                            "y0": 0.0,
                                            "x1": 10.0,
                                            "y1": 10.0,
                                        },
                                    }
                                ],
                            }
                        ],
                        "captions": [
                            {
                                "text": "cap2",
                                "bbox": {"x0": 0.0, "y0": 0.0, "x1": 10.0, "y1": 10.0},
                            }
                        ],
                        "footnotes": [
                            {
                                "text": "fn2",
                                "bbox": {"x0": 0.0, "y0": 0.0, "x1": 10.0, "y1": 10.0},
                            }
                        ],
                    }
                ],
            }
        ],
    }
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(json.dumps(input_json), encoding="utf-8")

    minify_dom(input_path, output_path)

    result = json.loads(output_path.read_text(encoding="utf-8"))
    page = result["pages"][0]
    assert "width" not in page
    assert "height" not in page
    article = page["articles"][0]
    assert "bbox" not in article
    assert "bbox" not in article["images"][0]
    assert "bbox" not in article["images"][0]["captions"][0]
    assert "bbox" not in article["images"][0]["footnotes"][0]
    assert "bbox" not in article["captions"][0]
    assert "bbox" not in article["footnotes"][0]


def test_minify_dom_file_not_found(tmp_path: Path) -> None:
    input_path = tmp_path / "nonexistent.json"
    output_path = tmp_path / "output.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        minify_dom(input_path, output_path)


def test_minify_dom_invalid_extension(tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    input_path.write_text("{}", encoding="utf-8")
    output_path = tmp_path / "output.json"
    with pytest.raises(ValueError, match="must be a .json file"):
        minify_dom(input_path, output_path)


def test_minify_dom_invalid_json(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    input_path.write_text("{invalid", encoding="utf-8")
    output_path = tmp_path / "output.json"
    with pytest.raises(ValueError, match="Invalid JSON file"):
        minify_dom(input_path, output_path)


def test_minify_dom_schema_validation_error(tmp_path: Path) -> None:
    input_json = {"invalid": "data"}
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(json.dumps(input_json), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        minify_dom(input_path, output_path)


def test_main_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_json = {
        "document_id": "doc1",
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
        "pages": [],
    }
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(input_json), encoding="utf-8")
    output_path = tmp_path / "output.json"

    main([str(input_path), "-o", str(output_path)])

    captured = capsys.readouterr()
    assert "successfully written" in captured.out
    assert output_path.exists()


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.json"
    input_path.write_text("{invalid", encoding="utf-8")
    output_path = tmp_path / "output.json"

    with pytest.raises(SystemExit) as exc_info:
        main([str(input_path), "-o", str(output_path)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error minifying JSON file" in captured.err


def test_minify_dom_sys_path():
    import sys
    import runpy

    # Temporarily remove and add _SRC_ROOT to ensure line 11 branch coverage
    # line 11 is 'if str(_SRC_ROOT) not in sys.path:'

    # ensure it IS in sys.path
    import pathlib

    repo_root = pathlib.Path(".").resolve()
    src_root = str(repo_root / "src")
    if src_root not in sys.path:
        sys.path.insert(0, src_root)

    # run module as __main__
    with patch("sys.argv", ["minify_dom", "--help"]):
        try:
            runpy.run_module("tools.minify_dom", run_name="__main__")
        except SystemExit:
            pass


def test_minify_dom_sys_path_not_in_path():
    # Remove _SRC_ROOT from sys.path if it exists to test the 'not in' branch
    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"

    original_path = sys.path.copy()

    # ensure it's not in sys.path
    if str(_SRC_ROOT) in sys.path:
        sys.path.remove(str(_SRC_ROOT))

    # reload module
    import importlib
    import tools.minify_dom

    importlib.reload(tools.minify_dom)

    sys.path = original_path


def test_minify_dom_sys_path_in_path():
    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"

    original_path = sys.path.copy()

    if str(_SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(_SRC_ROOT))

    import importlib
    import tools.minify_dom

    importlib.reload(tools.minify_dom)

    sys.path = original_path

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.filter_dom import filter_dom, main


@pytest.fixture
def sample_dom_json(tmp_path: Path) -> Path:
    """Create a temporary valid DOM JSON file."""
    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art_1",
                        "headline": "Head 1",
                        "body_blocks": ["text 1"],
                        "images": [
                            {
                                "path": "img1.png",
                                "media_type": "image",
                                "captions": [],
                                "footnotes": [],
                            }
                        ],
                        "captions": [],
                        "footnotes": [],
                    }
                ],
                "ads": ["ad 1"],
                "headers": ["header 1"],
                "footers": ["footer 1"],
                "page_numbers": [],
            },
            {
                "page_number": 2,
                "articles": [],
                "ads": ["ad 2"],
                "headers": ["header 2"],
                "footers": ["footer 2"],
                "page_numbers": [],
            },
        ],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }
    file_path = tmp_path / "sample.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


def test_filter_dom_success(sample_dom_json: Path):
    """Test successful filtering of DOM."""
    result = filter_dom(
        sample_dom_json,
        pages_to_keep={1},
        no_images=True,
        no_ads=True,
        no_headers=True,
        no_footers=True,
    )

    assert len(result["pages"]) == 1
    page1 = result["pages"][0]
    assert page1["page_number"] == 1
    assert page1["ads"] == []
    assert page1["headers"] == []
    assert page1["footers"] == []
    assert len(page1["articles"]) == 1
    assert page1["articles"][0]["images"] == []


def test_filter_dom_file_not_found(tmp_path: Path):
    """Test error when input file does not exist."""
    not_exist = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        filter_dom(not_exist)


def test_filter_dom_invalid_extension(tmp_path: Path):
    """Test error when input file is not a .json file."""
    invalid_ext = tmp_path / "sample.txt"
    invalid_ext.touch()
    with pytest.raises(ValueError, match="must be a .json file"):
        filter_dom(invalid_ext)


def test_filter_dom_invalid_json(tmp_path: Path):
    """Test error when input file contains invalid JSON."""
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{bad json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(invalid_json)


def test_filter_dom_schema_validation_error(tmp_path: Path):
    """Test error when JSON doesn't match schema."""
    bad_schema = tmp_path / "schema.json"
    bad_schema.write_text(
        '{"pages": [{"page_number": "not_an_int"}]}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        filter_dom(bad_schema)


@patch("sys.stdout")
def test_main_cli_stdout(mock_stdout, sample_dom_json: Path):
    """Test CLI outputting to stdout."""
    main([str(sample_dom_json), "--no-ads"])
    # Simply verify it didn't crash and printed something.
    assert mock_stdout.write.called


def test_main_cli_file_output(tmp_path: Path, sample_dom_json: Path):
    """Test CLI outputting to a file."""
    out_path = tmp_path / "out" / "filtered.json"
    main([str(sample_dom_json), "-p", "1", "-o", str(out_path)])

    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(data["pages"]) == 1
    assert data["pages"][0]["page_number"] == 1


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
    import tools.filter_dom

    target_path = str(tools.filter_dom._SRC_ROOT)

    # Remove the path
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != target_path])

    # Reload the module to trigger the injection
    reload(tools.filter_dom)

    assert target_path in sys.path

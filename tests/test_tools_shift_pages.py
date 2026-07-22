from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.shift_pages import shift_pages, main


@pytest.fixture
def sample_dom_path(tmp_path: Path) -> Path:
    """Fixture providing a sample DOM for page shifting."""
    data = {
        "pages": [
            {"page_number": 1, "articles": []},
            {"page_number": 3, "articles": []},
        ]
    }
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_shift_pages_positive(sample_dom_path: Path) -> None:
    """Test shifting page numbers with a positive offset."""
    result = shift_pages(sample_dom_path, offset=2)
    pages = result.get("pages", [])
    assert len(pages) == 2
    assert pages[0]["page_number"] == 3
    assert pages[1]["page_number"] == 5


def test_shift_pages_negative_with_floor(sample_dom_path: Path) -> None:
    """Test shifting page numbers with a negative offset and max(1) boundary."""
    result = shift_pages(sample_dom_path, offset=-2)
    pages = result.get("pages", [])
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1  # 1 - 2 = -1, max(1, -1) = 1
    assert pages[1]["page_number"] == 1  # 3 - 2 = 1, max(1, 1) = 1


def test_shift_pages_invalid_file(tmp_path: Path) -> None:
    """Test error handling for non-existent file."""
    path = tmp_path / "not_found.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        shift_pages(path, 1)


def test_shift_pages_invalid_extension(tmp_path: Path) -> None:
    """Test error handling for non-json extension."""
    path = tmp_path / "data.txt"
    path.write_text("{}")
    with pytest.raises(ValueError, match="must be a .json file"):
        shift_pages(path, 1)


def test_shift_pages_invalid_json(tmp_path: Path) -> None:
    """Test error handling for malformed JSON."""
    path = tmp_path / "bad.json"
    path.write_text("{bad json")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        shift_pages(path, 1)


def test_main_shift(
    sample_dom_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test main entry point with offset."""
    out_path = tmp_path / "out.json"
    main([str(sample_dom_path), str(out_path), "1"])

    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    assert pages[0]["page_number"] == 2
    assert pages[1]["page_number"] == 4

    captured = capsys.readouterr()
    assert "Shifted DOM saved to" in captured.out


def test_main_error_handling(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test main entry point error catch."""
    out_path = tmp_path / "out.json"
    not_found = tmp_path / "nope.json"
    with pytest.raises(SystemExit) as exc:
        main([str(not_found), str(out_path), "1"])
    assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "Error: File not found" in captured.err

def test_shift_pages_no_page_number(tmp_path: Path) -> None:
    """Test shifting page numbers when a page doesn't have a valid page_number."""
    data = {
        "pages": [
            {
                "articles": []
            },
            {
                "page_number": "not_an_int",
                "articles": []
            }
        ]
    }
    path = tmp_path / "sample_no_page.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    result = shift_pages(path, offset=2)
    pages = result.get("pages", [])
    assert len(pages) == 2
    assert "page_number" not in pages[0]
    assert pages[1]["page_number"] == "not_an_int"

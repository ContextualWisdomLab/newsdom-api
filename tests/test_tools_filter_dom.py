from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.filter_dom import filter_dom, main


@pytest.fixture
def sample_dom_path(tmp_path: Path) -> Path:
    """Fixture providing a sample DOM for filtering."""
    data = {
        "pages": [
            {
                "page_number": 1,
                "articles": [{"article_id": "a1", "images": [{"path": "img1.png"}]}],
            },
            {
                "page_number": 2,
                "articles": [{"article_id": "a2", "images": [{"path": "img2.png"}]}],
            },
            {"page_number": 3, "articles": [{"article_id": "a3", "images": []}]},
        ]
    }
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_filter_dom_pages_to_keep(sample_dom_path: Path) -> None:
    """Test filtering by specific page numbers."""
    result = filter_dom(sample_dom_path, pages_to_keep=[1, 3])
    pages = result.get("pages", [])
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert pages[1]["page_number"] == 3


def test_filter_dom_remove_images(sample_dom_path: Path) -> None:
    """Test removing images from DOM."""
    result = filter_dom(sample_dom_path, remove_images=True)
    pages = result.get("pages", [])
    assert len(pages) == 3
    assert len(pages[0]["articles"][0]["images"]) == 0
    assert len(pages[1]["articles"][0]["images"]) == 0


def test_filter_dom_invalid_file(tmp_path: Path) -> None:
    """Test error handling for non-existent file."""
    path = tmp_path / "not_found.json"
    with pytest.raises(FileNotFoundError, match="File not found"):
        filter_dom(path)


def test_filter_dom_invalid_extension(tmp_path: Path) -> None:
    """Test error handling for non-json extension."""
    path = tmp_path / "data.txt"
    path.write_text("{}")
    with pytest.raises(ValueError, match="must be a .json file"):
        filter_dom(path)


def test_filter_dom_invalid_json(tmp_path: Path) -> None:
    """Test error handling for malformed JSON."""
    path = tmp_path / "bad.json"
    path.write_text("{bad json")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(path)


def test_main_filter(
    sample_dom_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test main entry point with page filtering and image removal."""
    out_path = tmp_path / "out.json"
    main([str(sample_dom_path), str(out_path), "--pages", "1,2", "--remove-images"])

    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    assert len(pages) == 2
    assert len(pages[0]["articles"][0]["images"]) == 0

    captured = capsys.readouterr()
    assert "Filtered DOM saved to" in captured.out


def test_main_invalid_pages(
    sample_dom_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test main entry point with invalid --pages format."""
    out_path = tmp_path / "out.json"
    with pytest.raises(SystemExit) as exc:
        main([str(sample_dom_path), str(out_path), "--pages", "1,x"])
    assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "must be a comma-separated list of integers" in captured.err


def test_main_error_handling(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test main entry point error catch."""
    out_path = tmp_path / "out.json"
    not_found = tmp_path / "nope.json"
    with pytest.raises(SystemExit) as exc:
        main([str(not_found), str(out_path)])
    assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "Error: File not found" in captured.err

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.filter_dom import filter_dom, main


@pytest.fixture
def mock_dom(tmp_path: Path) -> Path:
    data = {
        "pages": [
            {"page_number": 1, "articles": [{"headline": "A"}]},
            {"page_number": 2, "articles": [{"headline": "B"}]},
            {"page_number": 3, "articles": [{"headline": "C"}]},
        ]
    }
    p = tmp_path / "mock.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_filter_dom_min_page(mock_dom: Path) -> None:
    res = filter_dom(mock_dom, min_page=2, max_page=None)
    assert len(res["pages"]) == 2
    assert res["pages"][0]["page_number"] == 2
    assert res["pages"][1]["page_number"] == 3


def test_filter_dom_max_page(mock_dom: Path) -> None:
    res = filter_dom(mock_dom, min_page=None, max_page=2)
    assert len(res["pages"]) == 2
    assert res["pages"][0]["page_number"] == 1
    assert res["pages"][1]["page_number"] == 2


def test_filter_dom_min_max_page(mock_dom: Path) -> None:
    res = filter_dom(mock_dom, min_page=2, max_page=2)
    assert len(res["pages"]) == 1
    assert res["pages"][0]["page_number"] == 2


def test_filter_dom_no_filter(mock_dom: Path) -> None:
    res = filter_dom(mock_dom, min_page=None, max_page=None)
    assert len(res["pages"]) == 3


def test_filter_dom_invalid_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="File not found"):
        filter_dom(tmp_path / "nonexistent.json", min_page=1, max_page=2)

    p = tmp_path / "mock.txt"
    p.write_text("hello")
    with pytest.raises(ValueError, match="must be a .json file"):
        filter_dom(p, min_page=1, max_page=2)


def test_filter_dom_invalid_range(mock_dom: Path) -> None:
    with pytest.raises(ValueError, match="min_page must be >= 1"):
        filter_dom(mock_dom, min_page=0, max_page=None)
    with pytest.raises(ValueError, match="max_page must be >= 1"):
        filter_dom(mock_dom, min_page=None, max_page=0)
    with pytest.raises(ValueError, match="min_page cannot be greater than max_page"):
        filter_dom(mock_dom, min_page=3, max_page=2)


def test_main_stdout(mock_dom: Path, capsys: pytest.CaptureFixture) -> None:
    main([str(mock_dom), "--min-page", "2", "--max-page", "3"])
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert len(res["pages"]) == 2


def test_main_file_output(mock_dom: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    main([str(mock_dom), "--min-page", "1", "--max-page", "1", "--output", str(out)])
    res = json.loads(out.read_text(encoding="utf-8"))
    assert len(res["pages"]) == 1


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit):
        main([str(tmp_path / "nonexistent.json")])
    captured = capsys.readouterr()
    assert "Error: File not found" in captured.err

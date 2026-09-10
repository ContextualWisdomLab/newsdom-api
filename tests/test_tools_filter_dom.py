"""Tests for the filter_dom tool."""

import json
from pathlib import Path
import pytest

from tools.filter_dom import filter_dom, parse_page_ranges, main


def test_parse_page_ranges():
    assert parse_page_ranges("1,2,3") == {1, 2, 3}
    assert parse_page_ranges("1-3") == {1, 2, 3}
    assert parse_page_ranges("1, 3-5, 7") == {1, 3, 4, 5, 7}
    assert parse_page_ranges("") == set()

    with pytest.raises(ValueError, match="Invalid page number"):
        parse_page_ranges("a")

    with pytest.raises(ValueError, match="Invalid page range"):
        parse_page_ranges("1-a")


def test_parse_page_ranges_requires_one_based_forward_ranges():
    for value in ("0", "-1", "0-2", "5-3"):
        with pytest.raises(ValueError, match="positive|range"):
            parse_page_ranges(value)


def test_filter_dom_valid(tmp_path):
    data = {
        "document_id": "doc1",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "a1",
                        "headline": "Head",
                        "images": [{"path": "img1"}],
                        "captions": [{"text": "cap1"}],
                        "body_blocks": ["text1"],
                    }
                ],
                "ads": ["ad1"],
                "headers": ["head1"],
                "footers": ["foot1"],
                "page_numbers": ["1"],
            },
            {
                "page_number": 2,
                "articles": [],
                "ads": ["ad2"],
                "headers": ["head2"],
                "footers": ["foot2"],
                "page_numbers": ["2"],
            },
        ],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }

    # Test exclude_images
    res = filter_dom(data, exclude_images=True)
    assert len(res["pages"][0]["articles"][0]["images"]) == 0
    assert len(res["pages"][0]["articles"][0]["captions"]) == 0

    # Test exclude_ads
    res = filter_dom(data, exclude_ads=True)
    assert len(res["pages"][0]["ads"]) == 0

    # Test exclude_headers_footers
    res = filter_dom(data, exclude_headers_footers=True)
    assert len(res["pages"][0]["headers"]) == 0
    assert len(res["pages"][0]["footers"]) == 0
    assert len(res["pages"][0]["page_numbers"]) == 0

    # Test pages_to_keep
    res = filter_dom(data, pages_to_keep={2})
    assert len(res["pages"]) == 1
    assert res["pages"][0]["page_number"] == 2


def test_filter_dom_invalid():
    with pytest.raises(ValueError, match="Invalid DOM JSON"):
        filter_dom({"invalid": "data"})


def test_main_success(tmp_path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {
        "document_id": "doc1",
        "pages": [
            {
                "page_number": 1,
                "articles": [],
                "ads": ["ad1"],
            }
        ],
        "quality": {"status": "success"},
    }
    input_file.write_text(json.dumps(data))

    main([str(input_file), str(output_file), "--exclude-ads", "--pages", "1"])
    assert output_file.exists()
    out_data = json.loads(output_file.read_text())
    assert len(out_data["pages"][0]["ads"]) == 0


def test_main_file_not_found(capsys, tmp_path):
    with pytest.raises(SystemExit) as excinfo:
        main([str(tmp_path / "nonexistent.json"), "out.json"])
    assert excinfo.value.code == 1
    assert "File not found" in capsys.readouterr().err


def test_main_invalid_json(capsys, tmp_path):
    input_file = tmp_path / "bad.json"
    input_file.write_text("not json")
    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), "out.json"])
    assert excinfo.value.code == 1
    assert "Error reading JSON" in capsys.readouterr().err


def test_main_invalid_pages(capsys, tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text("{}")
    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), "out.json", "--pages", "a"])
    assert excinfo.value.code == 1
    assert "Error parsing pages" in capsys.readouterr().err


def test_main_invalid_dom(capsys, tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text('{"bad": "schema"}')
    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), "out.json"])
    assert excinfo.value.code == 1
    assert "Error filtering DOM" in capsys.readouterr().err


def test_main_write_error(capsys, tmp_path, monkeypatch):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    data = {"document_id": "doc1", "pages": [], "quality": {"status": "success"}}
    input_file.write_text(json.dumps(data))

    def mock_write(*args, **kwargs):
        raise OSError("write failed")

    monkeypatch.setattr(Path, "write_text", mock_write)

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), str(output_file)])
    assert excinfo.value.code == 1
    assert "Error writing output file" in capsys.readouterr().err

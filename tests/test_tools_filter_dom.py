from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.filter_dom import filter_dom, main


def test_filter_dom_file_not_found(tmp_path: Path):
    input_path = tmp_path / "not_found.json"
    output_path = tmp_path / "out.json"
    with pytest.raises(FileNotFoundError, match=r"File not found"):
        filter_dom(input_path, output_path)


def test_filter_dom_not_json(tmp_path: Path):
    input_path = tmp_path / "input.txt"
    input_path.write_text("hello")
    output_path = tmp_path / "out.json"
    with pytest.raises(ValueError, match=r"must be a \.json file"):
        filter_dom(input_path, output_path)


def test_filter_dom_invalid_json(tmp_path: Path):
    input_path = tmp_path / "input.json"
    input_path.write_text("{invalid")
    output_path = tmp_path / "out.json"
    with pytest.raises(ValueError, match=r"Invalid JSON file"):
        filter_dom(input_path, output_path)


def test_filter_dom_success_all_branches(tmp_path: Path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "out.json"
    data = {
        "pages": [
            {
                "page_number": 1,  # skipped due to start_page=2
                "articles": [
                    {"headline": "Test 1", "images": [{"path": "img1.png"}]},
                ],
            },
            {
                "page_number": 2,  # included
                "articles": [
                    {
                        "headline": "tArGeT Article",
                        "images": [{"path": "img2.png"}],
                    },  # target matched, images removed
                    {"headline": "Other Article"},  # filtered out by headline
                    {
                        "headline": "TARGET 2",
                        "images": [{"path": "img3.png"}],
                    },  # target matched, images removed
                ],
            },
            {
                "page_number": 3,  # skipped due to end_page=2
                "articles": [{"headline": "Target 3"}],
            },
        ]
    }
    input_path.write_text(json.dumps(data))

    filter_dom(
        input_path,
        output_path,
        start_page=2,
        end_page=2,
        headline_regex="Target",
        remove_images=True,
    )

    assert output_path.exists()
    out_data = json.loads(output_path.read_text())
    pages = out_data["pages"]
    assert len(pages) == 1
    assert pages[0]["page_number"] == 2
    assert len(pages[0]["articles"]) == 2
    assert pages[0]["articles"][0]["headline"] == "tArGeT Article"
    assert pages[0]["articles"][0]["images"] == []
    assert pages[0]["articles"][1]["headline"] == "TARGET 2"
    assert pages[0]["articles"][1]["images"] == []


def test_filter_dom_no_filters(tmp_path: Path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "out.json"
    data = {
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"headline": "A", "images": [{"path": "img1.png"}]},
                    {"headline": "B"},  # No images key
                ],
            }
        ]
    }
    input_path.write_text(json.dumps(data))

    # Test without regex and remove_images=False
    filter_dom(input_path, output_path, remove_images=False)

    out_data = json.loads(output_path.read_text())
    pages = out_data["pages"]
    assert len(pages) == 1
    assert len(pages[0]["articles"]) == 2
    assert pages[0]["articles"][0]["images"] == [{"path": "img1.png"}]


def test_main_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "out.json"
    input_path.write_text('{"pages": []}')

    monkeypatch.setattr(
        "sys.argv", ["filter_dom.py", str(input_path), str(output_path)]
    )
    main()

    out, err = capsys.readouterr()
    assert "Filtered DOM successfully written" in out
    assert output_path.exists()


def test_main_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    input_path = tmp_path / "not_found.json"
    output_path = tmp_path / "out.json"

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_path), str(output_path)])

    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert "Error: File not found" in err


def test_filter_dom_remove_images_missing_images_key(tmp_path: Path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "out.json"
    data = {
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "headline": "B"
                    }  # No images key, testing remove_images branch (53->56)
                ],
            }
        ]
    }
    input_path.write_text(json.dumps(data))

    # Test remove_images=True but article doesn't have "images" key
    filter_dom(input_path, output_path, remove_images=True)

    out_data = json.loads(output_path.read_text())
    assert "images" not in out_data["pages"][0]["articles"][0]


def test_filter_dom_path_traversal(tmp_path: Path):
    input_path = tmp_path / "input.json"
    data = {"pages": []}
    input_path.write_text(json.dumps(data))

    # Use absolute path outside cwd and temp
    output_path = Path("/etc/evil.json")

    with pytest.raises(
        ValueError,
        match=r"Output path must be within the current working directory or temp directory",
    ):
        filter_dom(input_path, output_path)

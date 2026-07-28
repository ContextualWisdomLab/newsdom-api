import json
from pathlib import Path

import pytest

from tools.filter_dom import filter_dom, main


@pytest.fixture
def sample_dom_path(tmp_path: Path) -> Path:
    """Create a temporary dummy NewsDOM JSON file."""
    data = {
        "document_id": "doc-123",
        "pages": [
            {
                "page_number": 1,
                "ads": ["Ad 1"],
                "headers": ["Header 1"],
                "footers": ["Footer 1"],
                "page_numbers": ["1"],
            },
            {
                "page_number": 2,
                "ads": ["Ad 2"],
                "headers": ["Header 2"],
                "footers": ["Footer 2"],
                "page_numbers": ["2"],
            },
            {
                "page_number": 3,
                "ads": ["Ad 3"],
                "headers": ["Header 3"],
                "footers": ["Footer 3"],
                "page_numbers": ["3"],
            },
        ],
    }
    file_path = tmp_path / "sample.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


def test_filter_dom_page_range(sample_dom_path: Path):
    """Test filtering by start and end page."""
    # Test start_page only
    res = filter_dom(sample_dom_path, start_page=2)
    assert len(res["pages"]) == 2
    assert res["pages"][0]["page_number"] == 2

    # Test end_page only
    res = filter_dom(sample_dom_path, end_page=2)
    assert len(res["pages"]) == 2
    assert res["pages"][-1]["page_number"] == 2

    # Test both
    res = filter_dom(sample_dom_path, start_page=2, end_page=2)
    assert len(res["pages"]) == 1
    assert res["pages"][0]["page_number"] == 2


def test_filter_dom_remove_elements(sample_dom_path: Path):
    """Test removing specific elements."""
    res = filter_dom(
        sample_dom_path,
        remove_ads=True,
        remove_headers=True,
        remove_footers=True,
        remove_page_numbers=True,
    )
    for page in res["pages"]:
        assert page["ads"] == []
        assert page["headers"] == []
        assert page["footers"] == []
        assert page["page_numbers"] == []


def test_filter_dom_invalid_input(tmp_path: Path):
    """Test error handling for invalid input files."""
    # File not found
    with pytest.raises(FileNotFoundError):
        filter_dom(tmp_path / "missing.json")

    # Not a JSON file
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not json")
    with pytest.raises(ValueError, match="must be a .json file"):
        filter_dom(txt_file)


def test_main_success_stdout(sample_dom_path: Path, capsys: pytest.CaptureFixture):
    """Test main function printing to stdout."""
    main([str(sample_dom_path), "--start-page", "2", "--end-page", "2", "--remove-ads"])

    captured = capsys.readouterr()
    output_json = json.loads(captured.out)

    assert len(output_json["pages"]) == 1
    assert output_json["pages"][0]["page_number"] == 2
    assert output_json["pages"][0]["ads"] == []
    assert output_json["pages"][0]["headers"] == ["Header 2"]


def test_main_success_file_output(
    sample_dom_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture
):
    """Test main function saving to output file."""
    out_file = tmp_path / "out.json"
    main(
        [
            str(sample_dom_path),
            "-o",
            str(out_file),
            "--remove-headers",
            "--remove-footers",
            "--remove-page-numbers",
        ]
    )

    captured = capsys.readouterr()
    assert "Filtered DOM saved to" in captured.out

    saved_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(saved_data["pages"]) == 3
    assert saved_data["pages"][0]["headers"] == []
    assert saved_data["pages"][0]["footers"] == []
    assert saved_data["pages"][0]["page_numbers"] == []
    assert saved_data["pages"][0]["ads"] == ["Ad 1"]


def test_main_error_handling(tmp_path: Path, capsys: pytest.CaptureFixture):
    """Test main function error handling."""
    missing_file = tmp_path / "does_not_exist.json"

    with pytest.raises(SystemExit) as exc_info:
        main([str(missing_file)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: File not found" in captured.err

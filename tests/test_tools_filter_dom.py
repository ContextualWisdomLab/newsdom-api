import json
import sys
from pathlib import Path

import pytest

from tools.filter_dom import filter_dom, main


def create_valid_parse_response_data() -> dict:
    return {
        "document_id": "test_doc",
        "quality": {"status": "success", "parser": "test", "warnings": []},
        "pages": [
            {
                "page_number": 1,
                "ads": ["Ad 1"],
                "headers": ["Header 1"],
                "footers": ["Footer 1"],
                "articles": [
                    {
                        "article_id": "art-1",
                        "headline": "H1",
                        "images": [{"path": "img1.png", "media_type": "image"}],
                        "body_blocks": [],
                    }
                ],
                "page_numbers": [],
            }
        ],
    }


def test_filter_dom_removes_elements(tmp_path: Path):
    input_file = tmp_path / "input.json"
    data = create_valid_parse_response_data()
    input_file.write_text(json.dumps(data))

    result = filter_dom(
        input_file,
        remove_ads=True,
        remove_images=True,
        remove_headers=True,
        remove_footers=True,
    )

    page = result["pages"][0]
    assert page["ads"] == []
    assert page["headers"] == []
    assert page["footers"] == []
    assert page["articles"][0]["images"] == []


def test_filter_dom_partial_removal(tmp_path: Path):
    input_file = tmp_path / "input.json"
    data = create_valid_parse_response_data()
    input_file.write_text(json.dumps(data))

    result = filter_dom(
        input_file,
        remove_ads=True,
        remove_images=True,
    )

    page = result["pages"][0]
    assert page["ads"] == []
    assert page["headers"] == ["Header 1"]
    assert page["footers"] == ["Footer 1"]
    assert page["articles"][0]["images"] == []


def test_filter_dom_no_removal(tmp_path: Path):
    input_file = tmp_path / "input.json"
    data = create_valid_parse_response_data()
    input_file.write_text(json.dumps(data))

    result = filter_dom(input_file)

    page = result["pages"][0]
    assert page["ads"] == ["Ad 1"]
    assert page["headers"] == ["Header 1"]
    assert page["footers"] == ["Footer 1"]
    assert page["articles"][0]["images"] == [
        {"path": "img1.png", "media_type": "image"}
    ]


def test_filter_dom_empty_pages(tmp_path: Path):
    input_file = tmp_path / "input.json"
    data = create_valid_parse_response_data()
    data["pages"] = []
    input_file.write_text(json.dumps(data))

    result = filter_dom(input_file, remove_ads=True)
    assert result["pages"] == []


def test_filter_dom_article_without_images(tmp_path: Path):
    input_file = tmp_path / "input.json"
    data = create_valid_parse_response_data()
    del data["pages"][0]["articles"][0]["images"]
    input_file.write_text(json.dumps(data))

    result = filter_dom(input_file, remove_images=True)
    assert "images" not in result["pages"][0]["articles"][0]


def test_filter_dom_not_a_file(tmp_path: Path):
    non_existent = tmp_path / "non_existent.json"
    with pytest.raises(FileNotFoundError):
        filter_dom(non_existent)


def test_filter_dom_wrong_extension(tmp_path: Path):
    txt_file = tmp_path / "input.txt"
    txt_file.write_text("{}")
    with pytest.raises(ValueError, match="must be a .json file"):
        filter_dom(txt_file)


def test_filter_dom_invalid_json(tmp_path: Path):
    input_file = tmp_path / "input.json"
    input_file.write_text("{invalid")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(input_file)


def test_filter_dom_invalid_schema(tmp_path: Path):
    input_file = tmp_path / "input.json"
    input_file.write_text('{"pages": []}')
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        filter_dom(input_file)


def test_main_with_output(tmp_path: Path, capsys):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = create_valid_parse_response_data()
    input_file.write_text(json.dumps(data))

    main([str(input_file), "-o", str(output_file), "--remove-ads"])

    assert output_file.is_file()
    result = json.loads(output_file.read_text())
    assert result["pages"][0]["ads"] == []


def test_main_without_output(tmp_path: Path, capsys):
    input_file = tmp_path / "input.json"
    data = create_valid_parse_response_data()
    input_file.write_text(json.dumps(data))

    main([str(input_file), "--remove-ads"])

    captured = capsys.readouterr()
    assert '"ads": []' in captured.out


def test_main_exception_filenotfound(tmp_path: Path, capsys):
    non_existent = tmp_path / "non_existent.json"
    with pytest.raises(SystemExit) as exc:
        main([str(non_existent)])

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_main_exception_valueerror(tmp_path: Path, capsys):
    input_file = tmp_path / "input.txt"
    input_file.write_text("")
    with pytest.raises(SystemExit) as exc:
        main([str(input_file)])

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "must be a .json file" in captured.err


def test_sys_path_injection_local_scope(monkeypatch, tmp_path: Path):
    """Test that sys.path injection is properly handled and cleaned up."""
    input_file = tmp_path / "input.json"
    data = create_valid_parse_response_data()
    input_file.write_text(json.dumps(data))

    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = str(_REPO_ROOT / "src")

    # Remove src from sys.path to force the function to inject it
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != _SRC_ROOT])

    assert _SRC_ROOT not in sys.path

    # Run filter_dom, which should locally inject and then remove _SRC_ROOT
    filter_dom(input_file)

    # Verify cleanup occurred
    assert _SRC_ROOT not in sys.path

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.filter_dom import filter_dom, main


@pytest.fixture
def sample_json_path(tmp_path: Path) -> Path:
    data = {
        "document_id": "test-doc",
        "pages": [
            {
                "page_number": 1,
                "ads": ["Ad 1", "Ad 2"],
                "headers": ["Header 1"],
                "footers": ["Footer 1"],
                "articles": [
                    {
                        "article_id": "article-1",
                        "headline": "Test Headline",
                        "captions": [{"text": "Caption 1"}],
                        "images": [
                            {"path": "img1.png", "captions": [{"text": "Img Cap 1"}]}
                        ],
                    }
                ],
            }
        ],
    }
    file_path = tmp_path / "test.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


def test_filter_dom_all_removed(sample_json_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "out.json"
    filter_dom(
        sample_json_path,
        output_path,
        remove_images=True,
        remove_captions=True,
        remove_ads=True,
        remove_headers=True,
        remove_footers=True,
    )

    assert output_path.exists()
    out_data = json.loads(output_path.read_text(encoding="utf-8"))
    page = out_data["pages"][0]

    assert page["ads"] == []
    assert page["headers"] == []
    assert page["footers"] == []
    assert page["articles"][0]["images"] == []
    assert page["articles"][0]["captions"] == []


def test_filter_dom_no_removal(sample_json_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "out.json"
    filter_dom(
        sample_json_path,
        output_path,
        remove_images=False,
        remove_captions=False,
        remove_ads=False,
        remove_headers=False,
        remove_footers=False,
    )

    assert output_path.exists()
    out_data = json.loads(output_path.read_text(encoding="utf-8"))
    page = out_data["pages"][0]

    assert len(page["ads"]) == 2
    assert len(page["headers"]) == 1
    assert len(page["footers"]) == 1
    assert len(page["articles"][0]["images"]) == 1
    assert len(page["articles"][0]["captions"]) == 1
    assert len(page["articles"][0]["images"][0]["captions"]) == 1


def test_filter_dom_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        filter_dom(tmp_path / "nonexistent.json", tmp_path / "out.json")


def test_filter_dom_invalid_extension(tmp_path: Path) -> None:
    invalid_file = tmp_path / "test.txt"
    invalid_file.touch()
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        filter_dom(invalid_file, tmp_path / "out.json")


def test_filter_dom_invalid_json(tmp_path: Path) -> None:
    invalid_json = tmp_path / "test.json"
    invalid_json.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(invalid_json, tmp_path / "out.json")


def test_main_success(sample_json_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    output_path = tmp_path / "out.json"
    main([
        str(sample_json_path),
        "-o", str(output_path),
        "--remove-ads",
        "--remove-images"
    ])

    captured = capsys.readouterr()
    assert "Filtered JSON successfully written to" in captured.out
    assert output_path.exists()

    out_data = json.loads(output_path.read_text(encoding="utf-8"))
    page = out_data["pages"][0]
    assert page["ads"] == []
    assert page["articles"][0]["images"] == []


def test_main_failure(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    output_path = tmp_path / "out.json"
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "nonexistent.json"), "-o", str(output_path)])

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Error filtering JSON file" in captured.err

def test_filter_dom_captions_without_images(sample_json_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "out.json"
    filter_dom(
        sample_json_path,
        output_path,
        remove_images=False,
        remove_captions=True,
    )

    assert output_path.exists()
    out_data = json.loads(output_path.read_text(encoding="utf-8"))
    page = out_data["pages"][0]

    assert page["articles"][0]["captions"] == []
    # Assert that image captions were removed
    assert page["articles"][0]["images"][0]["captions"] == []
    # Assert images were NOT removed
    assert len(page["articles"][0]["images"]) == 1

def test_filter_dom_empty_images(sample_json_path: Path, tmp_path: Path) -> None:
    # Modify data to have an article without images array to cover the get fallback
    data = json.loads(sample_json_path.read_text(encoding="utf-8"))
    del data["pages"][0]["articles"][0]["images"]
    sample_json_path.write_text(json.dumps(data), encoding="utf-8")

    output_path = tmp_path / "out.json"
    filter_dom(
        sample_json_path,
        output_path,
        remove_captions=True,
    )

    out_data = json.loads(output_path.read_text(encoding="utf-8"))
    assert out_data["pages"][0]["articles"][0]["captions"] == []

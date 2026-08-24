from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.extract_images import extract_images, main


def test_extract_images_success(tmp_path: Path):
    json_path = tmp_path / "valid.json"
    valid_data = {
        "document_id": "doc123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "images": [
                            {
                                "path": "images/img1.jpg",
                                "captions": [{"text": "Caption 1"}]
                            },
                            {
                                "path": "images/img2.png",
                                "captions": ["Caption 2", {"text": "Caption 3"}]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    json_path.write_text(json.dumps(valid_data), encoding="utf-8")

    images = extract_images(json_path)
    assert len(images) == 2
    assert images[0]["path"] == "images/img1.jpg"
    assert images[0]["captions"] == ["Caption 1"]
    assert images[0]["page_number"] == 1

    assert images[1]["path"] == "images/img2.png"
    assert images[1]["captions"] == ["Caption 2", "Caption 3"]
    assert images[1]["page_number"] == 1


def test_extract_images_file_not_found(tmp_path: Path):
    non_existent = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        extract_images(non_existent)


def test_extract_images_invalid_extension(tmp_path: Path):
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="File must be a .json file"):
        extract_images(txt_path)


def test_main_stdout(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    json_path = tmp_path / "valid.json"
    valid_data = {
        "pages": [
            {
                "page_number": 2,
                "articles": [
                    {
                        "images": [
                            {"path": "img.jpg"}
                        ]
                    }
                ]
            }
        ]
    }
    json_path.write_text(json.dumps(valid_data), encoding="utf-8")

    main([str(json_path)])
    out = capsys.readouterr().out
    assert "img.jpg" in out

    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["path"] == "img.jpg"
    assert data[0]["page_number"] == 2


def test_main_output_file(tmp_path: Path):
    json_path = tmp_path / "valid.json"
    valid_data = {
        "pages": [
            {
                "articles": [
                    {
                        "images": [
                            {"path": "test.png", "captions": [{"text": "test caption"}]}
                        ]
                    }
                ]
            }
        ]
    }
    json_path.write_text(json.dumps(valid_data), encoding="utf-8")

    output_path = tmp_path / "output.json"
    main([str(json_path), "-o", str(output_path)])

    assert output_path.exists()
    out_data = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(out_data) == 1
    assert out_data[0]["path"] == "test.png"
    assert out_data[0]["captions"] == ["test caption"]
    assert out_data[0]["page_number"] is None


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    non_existent = tmp_path / "missing.json"

    with pytest.raises(SystemExit) as exc_info:
        main([str(non_existent)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "File not found" in captured.err

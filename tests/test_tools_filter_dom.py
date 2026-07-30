import json
from pathlib import Path

import pytest
from tools.filter_dom import filter_dom, main


def test_filter_dom_success(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {
        "pages": [
            {
                "articles": [
                    {
                        "body_blocks": [
                            {"type": "text", "text": "Text 1"},
                            {"type": "image", "image_id": "img1"},
                            {"type": "text", "text": "Text 2"},
                        ]
                    }
                ]
            }
        ]
    }
    input_file.write_text(json.dumps(data), encoding="utf-8")

    filter_dom(input_file, "text", output_file)

    assert output_file.exists()
    result = json.loads(output_file.read_text(encoding="utf-8"))

    blocks = result["pages"][0]["articles"][0]["body_blocks"]
    assert len(blocks) == 2
    assert blocks[0]["type"] == "text"
    assert blocks[1]["type"] == "text"


def test_filter_dom_all(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {
        "pages": [
            {
                "articles": [
                    {
                        "body_blocks": [
                            {"type": "text", "text": "Text 1"},
                            {"type": "image", "image_id": "img1"},
                        ]
                    }
                ]
            }
        ]
    }
    input_file.write_text(json.dumps(data), encoding="utf-8")

    filter_dom(input_file, "all", output_file)

    assert output_file.exists()
    result = json.loads(output_file.read_text(encoding="utf-8"))

    blocks = result["pages"][0]["articles"][0]["body_blocks"]
    assert len(blocks) == 2


def test_filter_dom_not_found(tmp_path: Path):
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    with pytest.raises(FileNotFoundError):
        filter_dom(input_file, "text", output_file)


def test_filter_dom_invalid_extension(tmp_path: Path):
    input_file = tmp_path / "input.txt"
    input_file.write_text("hello", encoding="utf-8")
    output_file = tmp_path / "output.json"

    with pytest.raises(ValueError, match="must be a .json file"):
        filter_dom(input_file, "text", output_file)


def test_main_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {
        "pages": [
            {
                "articles": [
                    {
                        "body_blocks": [
                            {"type": "text", "text": "Text 1"},
                        ]
                    }
                ]
            }
        ]
    }
    input_file.write_text(json.dumps(data), encoding="utf-8")

    main([str(input_file), str(output_file), "--type", "text"])

    assert output_file.exists()
    captured = capsys.readouterr()
    assert f"Filtered DOM saved to: {output_file}" in captured.out


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), str(output_file), "--type", "text"])

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_filter_dom_empty_blocks(tmp_path: Path):
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {
        "pages": [
            {
                "articles": [
                    {
                        "body_blocks": [
                            {"type": "image", "image_id": "img1"},
                        ]
                    }
                ]
            },
            {"articles": [{}]},
        ]
    }
    input_file.write_text(json.dumps(data), encoding="utf-8")

    filter_dom(input_file, "text", output_file)

    assert output_file.exists()
    result = json.loads(output_file.read_text(encoding="utf-8"))

    assert len(result["pages"]) == 0

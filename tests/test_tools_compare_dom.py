import json
from pathlib import Path

import pytest
from tools.compare_dom import compare_dom, main


def test_compare_dom_success(tmp_path: Path):
    file1 = tmp_path / "file1.json"
    file2 = tmp_path / "file2.json"

    data1 = {
        "pages": [
            {
                "articles": [
                    {
                        "body_blocks": [
                            {"type": "text"},
                            {"type": "image"},
                        ]
                    }
                ]
            }
        ]
    }

    data2 = {
        "pages": [
            {
                "articles": [
                    {
                        "body_blocks": [
                            {"type": "text"},
                        ]
                    }
                ]
            }
        ]
    }

    file1.write_text(json.dumps(data1), encoding="utf-8")
    file2.write_text(json.dumps(data2), encoding="utf-8")

    result = compare_dom(file1, file2)

    assert result["file1"]["num_pages"] == 1
    assert result["file1"]["num_blocks"] == 2
    assert result["file1"]["num_images"] == 1

    assert result["file2"]["num_pages"] == 1
    assert result["file2"]["num_blocks"] == 1
    assert result["file2"]["num_images"] == 0

    assert result["diff"]["num_blocks"] == 1
    assert result["diff"]["num_images"] == 1


def test_compare_dom_not_found(tmp_path: Path):
    file1 = tmp_path / "file1.json"
    file2 = tmp_path / "file2.json"

    file1.write_text("{}", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        compare_dom(file1, file2)


def test_compare_dom_invalid_extension(tmp_path: Path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.json"

    file1.write_text("{}", encoding="utf-8")
    file2.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a .json file"):
        compare_dom(file1, file2)


def test_main_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    file1 = tmp_path / "file1.json"
    file2 = tmp_path / "file2.json"

    file1.write_text(json.dumps({"pages": []}), encoding="utf-8")
    file2.write_text(json.dumps({"pages": []}), encoding="utf-8")

    main([str(file1), str(file2)])

    captured = capsys.readouterr()
    assert "DOM Comparison Report" in captured.out
    assert "Diff=0" in captured.out


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    file1 = tmp_path / "file1.json"
    file2 = tmp_path / "file2.json"

    file1.write_text(json.dumps({"pages": []}), encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main([str(file1), str(file2)])

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err

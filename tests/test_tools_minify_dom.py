import json
from pathlib import Path
import pytest

from tools.minify_dom import minify_dom, main


@pytest.fixture
def sample_dom_json(tmp_path: Path) -> Path:
    data = {
        "document_id": "test_doc",
        "bbox": {"x0": 0, "y0": 0, "x1": 100, "y1": 100},
        "pages": [
            {
                "page_number": 1,
                "bbox": {"x0": 10, "y0": 10, "x1": 50, "y1": 50},
                "articles": [
                    {
                        "article_id": "art_1",
                        "bbox": {"x0": 20, "y0": 20, "x1": 40, "y1": 40},
                        "headline": "Test"
                    }
                ]
            }
        ]
    }
    file_path = tmp_path / "test.json"
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return file_path


def test_minify_dom_logic(sample_dom_json: Path, tmp_path: Path):
    output_path = tmp_path / "minified.json"
    minify_dom(sample_dom_json, output_path)

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert "bbox" not in result
    assert "bbox" not in result["pages"][0]
    assert "bbox" not in result["pages"][0]["articles"][0]
    assert result["document_id"] == "test_doc"

    # Check for minification (no spaces)
    raw_text = output_path.read_text(encoding="utf-8")
    assert " " not in raw_text
    assert "\n" not in raw_text


def test_minify_dom_invalid_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        minify_dom(tmp_path / "missing.json", tmp_path / "out.json")

    invalid_ext = tmp_path / "test.txt"
    invalid_ext.write_text("hello")
    with pytest.raises(ValueError, match="must be a .json file"):
        minify_dom(invalid_ext, tmp_path / "out.json")

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("invalid data")
    with pytest.raises(ValueError, match="Invalid JSON"):
        minify_dom(invalid_json, tmp_path / "out.json")


def test_main_cli(sample_dom_json: Path, tmp_path: Path, capsys):
    output_path = tmp_path / "out.json"
    main([str(sample_dom_json), "-o", str(output_path)])

    assert output_path.exists()
    out, _ = capsys.readouterr()
    assert "successfully" in out


def test_main_cli_error(tmp_path: Path, monkeypatch):
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "missing.json"), "-o", str(tmp_path / "out.json")])
    assert exc_info.value.code == 1

import json
import pytest
from pathlib import Path
from tools.extract_text import extract_text, main


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "valid.json"

    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "headers": ["Test Header"],
                "articles": [
                    {
                        "headline": "Test Headline",
                        "body_blocks": ["Test Body 1", "Test Body 2"]
                    }
                ],
                "footers": ["Test Footer"]
            },
            "invalid_page",
            {
                "page_number": 2,
                "articles": [
                    "invalid_article",
                    {
                        "headline": "",
                        "body_blocks": []
                    }
                ]
            },
            {
                "articles": [
                    {
                        "headline": "No Page Number Article",
                        "body_blocks": ["No Page Number Body"]
                    }
                ]
            }
        ],
        "quality": {"status": "success", "parser": "mineru", "warnings": []}
    }

    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


@pytest.fixture
def empty_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "empty.json"
    json_path.write_text("{}", encoding="utf-8")
    return json_path


def test_extract_text_success(mock_json_file: Path):
    result = extract_text(mock_json_file)
    assert "Document: test_doc" in result
    assert "--- Page 1 ---" in result
    assert "Test Header" in result
    assert "Test Headline" in result
    assert "Test Body 1" in result
    assert "Test Body 2" in result
    assert "Test Footer" in result
    assert "--- Page 2 ---" in result


def test_extract_text_empty(empty_json_file: Path):
    result = extract_text(empty_json_file)
    assert result == ""


def test_extract_text_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        extract_text(tmp_path / "nonexistent.json")


def test_extract_text_wrong_ext(tmp_path: Path):
    txt = tmp_path / "test.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(ValueError):
        extract_text(txt)


def test_main_success_stdout(mock_json_file: Path, capsys: pytest.CaptureFixture[str]):
    main([str(mock_json_file)])
    captured = capsys.readouterr()
    assert "Document: test_doc" in captured.out
    assert "Test Headline" in captured.out


def test_main_success_file_output(
    mock_json_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    out_file = tmp_path / "out.txt"
    main([str(mock_json_file), "-o", str(out_file)])
    captured = capsys.readouterr()
    assert "Text written to" in captured.out
    content = out_file.read_text(encoding="utf-8")
    assert "Document: test_doc" in content
    assert "Test Headline" in content


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as e:
        main([str(tmp_path / "nonexistent.json")])
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error extracting text:" in captured.err

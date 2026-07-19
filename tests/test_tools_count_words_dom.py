from pathlib import Path
import json
import pytest

from tools.count_words_dom import count_words_dom, main


@pytest.fixture
def mock_dom_data():
    return {
        "pages": [
            {
                "articles": [
                    {
                        "headline": "Hello World",
                        "body_blocks": ["This is a test block.", "Another one."],
                    }
                ]
            },
            {"articles": []},
        ]
    }


def test_count_words_dom_success(tmp_path: Path, mock_dom_data: dict):
    test_json = tmp_path / "test.json"
    test_json.write_text(json.dumps(mock_dom_data), encoding="utf-8")

    stats = count_words_dom(test_json)

    # "Hello World" -> 2 words, 11 chars
    # "This is a test block." -> 5 words, 21 chars
    # "Another one." -> 2 words, 12 chars
    # Total words: 2 + 5 + 2 = 9
    # Total chars: 11 + 21 + 12 = 44
    assert stats["total_words"] == 9
    assert stats["total_chars"] == 44


def test_count_words_dom_empty_blocks(tmp_path: Path):
    test_json = tmp_path / "test.json"
    test_json.write_text(
        json.dumps({"pages": [{"articles": [{"headline": "", "body_blocks": [""]}]}]}),
        encoding="utf-8",
    )

    stats = count_words_dom(test_json)

    assert stats["total_words"] == 0
    assert stats["total_chars"] == 0


def test_count_words_dom_file_not_found():
    with pytest.raises(FileNotFoundError):
        count_words_dom(Path("nonexistent.json"))


def test_count_words_dom_invalid_extension(tmp_path: Path):
    test_txt = tmp_path / "test.txt"
    test_txt.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="File must be a .json file"):
        count_words_dom(test_txt)


def test_main_success(
    tmp_path: Path, mock_dom_data: dict, capsys: pytest.CaptureFixture
):
    test_json = tmp_path / "test.json"
    test_json.write_text(json.dumps(mock_dom_data), encoding="utf-8")

    main([str(test_json)])
    captured = capsys.readouterr()

    assert "Total Words: 9" in captured.out
    assert "Total Characters: 44" in captured.out


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent.json"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err

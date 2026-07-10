from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import tools.extract_text as extract_text


@pytest.fixture
def sample_newsdom_json(tmp_path: Path) -> Path:
    p = tmp_path / "sample.json"
    p.write_text(
        """
        {
            "document_id": "test_doc",
            "pages": [
                {
                    "headers": ["Top Header", null],
                    "articles": [
                        {
                            "headline": "Main News",
                            "body_blocks": ["Body paragraph 1.", null],
                            "images": [
                                {
                                    "path": "img1.png",
                                    "captions": [{"text": "Image 1 Caption"}, "String Caption", null]
                                },
                                "not_a_dict"
                            ],
                            "captions": [{"text": "Article Caption"}, null],
                            "footnotes": [{"text": "Article Footnote"}, null]
                        },
                        "not_a_dict"
                    ],
                    "ads": ["Advertisement Text", null],
                    "footers": ["Page 1 Footer", null]
                },
                "not_a_dict"
            ]
        }
        """,
        encoding="utf-8",
    )
    return p


def test_extract_plain_text(sample_newsdom_json: Path) -> None:
    import json

    data = json.loads(sample_newsdom_json.read_text(encoding="utf-8"))
    text = extract_text.extract_plain_text(data)

    assert "Top Header" in text
    assert "Main News" in text
    assert "Body paragraph 1." in text
    assert "Image 1 Caption" in text
    assert "String Caption" in text
    assert "Article Caption" in text
    assert "Article Footnote" in text
    assert "Advertisement Text" in text
    assert "Page 1 Footer" in text
    # Ensure 'None' string representation is not inserted when filtering empty nodes
    assert "None" not in text


def test_extract_plain_text_empty_data() -> None:
    assert extract_text.extract_plain_text({}) == ""


def test_extract_plain_text_invalid_pages() -> None:
    assert extract_text.extract_plain_text({"pages": "not_a_list"}) == ""


def test_extract_plain_text_invalid_page() -> None:
    assert extract_text.extract_plain_text({"pages": ["string_page"]}) == ""


def test_extract_plain_text_invalid_article() -> None:
    data = {"pages": [{"articles": ["string_article"]}]}
    assert extract_text.extract_plain_text(data) == ""


def test_extract_plain_text_invalid_image() -> None:
    data = {"pages": [{"articles": [{"images": ["string_image"]}]}]}
    assert extract_text.extract_plain_text(data) == ""


def test_main_stdout(
    sample_newsdom_json: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with patch("sys.argv", ["extract_text.py", str(sample_newsdom_json)]):
        extract_text.main()
    captured = capsys.readouterr()
    assert "Top Header" in captured.out
    assert "Main News" in captured.out


def test_main_output_file(
    sample_newsdom_json: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out_file = tmp_path / "out.txt"
    with patch(
        "sys.argv", ["extract_text.py", str(sample_newsdom_json), "-o", str(out_file)]
    ):
        extract_text.main()

    captured = capsys.readouterr()
    assert "Extracted text written" in captured.out

    out_text = out_file.read_text(encoding="utf-8")
    assert "Top Header" in out_text


def test_main_file_not_found(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    not_exist = tmp_path / "does_not_exist.json"
    with patch("sys.argv", ["extract_text.py", str(not_exist)]):
        with pytest.raises(SystemExit) as exc:
            extract_text.main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "File not found or is not a file" in captured.err


def test_main_invalid_extension(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    txt_file = tmp_path / "test.txt"
    txt_file.touch()
    with patch("sys.argv", ["extract_text.py", str(txt_file)]):
        with pytest.raises(SystemExit) as exc:
            extract_text.main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Input file must be a .json file" in captured.err

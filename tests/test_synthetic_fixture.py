from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest

from newsdom_api.synthetic import (
    _draw_vertical_text,
    _ground_truth,
    _split_vertical,
    generate_fixture,
)


def test_generate_fixture_writes_pdf_and_truth(tmp_path: Path):
    pdf_path, truth_path = generate_fixture(tmp_path, seed=7)
    assert pdf_path.exists()
    assert truth_path.exists()


@pytest.mark.parametrize(
    "text, max_chars, expected",
    [
        ("abcdefgh", 3, ["abc", "def", "gh"]),
        ("abcdef", 3, ["abc", "def"]),
        ("a", 3, ["a"]),
        ("", 3, []),
        ("abcdef", 1, ["a", "b", "c", "d", "e", "f"]),
        ("abcdef", 10, ["abcdef"]),
    ],
)
def test_split_vertical(text: str, max_chars: int, expected: list[str]):
    assert _split_vertical(text, max_chars) == expected


def test_draw_vertical_text():
    mock_draw = Mock()
    mock_font = Mock()

    _draw_vertical_text(mock_draw, "ABC", 10, 20, mock_font, 15)

    expected_calls = [
        call((10, 20), "A", fill="black", font=mock_font),
        call((10, 35), "B", fill="black", font=mock_font),
        call((10, 50), "C", fill="black", font=mock_font),
    ]

    mock_draw.text.assert_has_calls(expected_calls)
    assert mock_draw.text.call_count == 3


def test_draw_vertical_text_empty():
    mock_draw = Mock()
    mock_font = Mock()

    _draw_vertical_text(mock_draw, "", 10, 20, mock_font, 15)

    mock_draw.text.assert_not_called()


def test_generate_fixture_early_break(tmp_path: Path):
    with patch("newsdom_api.synthetic._ground_truth") as mock_truth:
        truth = _ground_truth()
        # Body bbox remains valid after margins but is too narrow for multiple columns.
        truth["articles"] = [
            {
                "headline": "A",
                "body": "BBBBBBBBBB",
                "bbox": [100, 10, 190, 420],
                "vertical": True,
                "page_number": 1,
            }
        ]
        truth["images"] = []
        truth["ads"] = []
        mock_truth.return_value = truth

        pdf_path, truth_path = generate_fixture(tmp_path, seed=9)
        assert pdf_path.exists()
        assert truth_path.exists()

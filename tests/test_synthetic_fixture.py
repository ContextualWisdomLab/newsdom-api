from pathlib import Path
from unittest.mock import Mock, call, patch

from newsdom_api.synthetic import _draw_vertical_text, _ground_truth, generate_fixture


def test_generate_fixture_writes_pdf_and_truth(tmp_path: Path):
    pdf_path, truth_path = generate_fixture(tmp_path, seed=7)
    assert pdf_path.exists()
    assert truth_path.exists()


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


def test_load_font_finds_candidate():
    with patch("newsdom_api.synthetic._font_candidates", return_value=["dummy_font.ttc"]), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("PIL.ImageFont.truetype") as mock_truetype:
        from newsdom_api.synthetic import _load_font
        _load_font(12)
        mock_truetype.assert_called_once_with("dummy_font.ttc", size=12)


def test_generate_fixture_horizontal_article(tmp_path: Path):
    with patch("newsdom_api.synthetic._ground_truth") as mock_truth:
        truth = _ground_truth()
        truth["articles"] = [
            {
                "headline": "Horizontal",
                "body": "This is a horizontal article.",
                "bbox": [10, 10, 100, 100],
                "vertical": False,
                "page_number": 1,
            }
        ]
        # Images and ads can be empty for this test
        truth["images"] = []
        truth["ads"] = []
        mock_truth.return_value = truth

        pdf_path, truth_path = generate_fixture(tmp_path, seed=8)
        assert pdf_path.exists()
        assert truth_path.exists()


def test_generate_fixture_early_break(tmp_path: Path):
    with patch("newsdom_api.synthetic._ground_truth") as mock_truth:
        truth = _ground_truth()
        # Bounding box width is smaller than font step
        truth["articles"] = [
            {
                "headline": "A",
                "body": "BBBBBBBBBB",
                "bbox": [100, 10, 110, 100],
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

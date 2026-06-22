from unittest.mock import patch
from PIL import Image, ImageDraw, ImageFont
from newsdom_api.synthetic import _safe_draw_text

def test_safe_draw_text_fallback():
    image = Image.new("L", (100, 100), color=245)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    # Mock draw.text to raise UnicodeEncodeError
    with patch.object(draw, 'text', side_effect=[UnicodeEncodeError('mock', '', 0, 1, 'mock'), None]) as mock_text:
        _safe_draw_text(draw, (10, 10), "こんにちは", font=font)
        # Should be called twice. First time it fails, second time with fallback.
        assert mock_text.call_count == 2
        # The fallback string is evaluated to '?????' since ord(c) for all characters in 'こんにちは' > 256
        mock_text.assert_called_with((10, 10), "?????", fill="black", font=font)

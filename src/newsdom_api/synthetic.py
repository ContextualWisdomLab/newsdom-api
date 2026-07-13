"""Synthetic newspaper fixture generation for redistributable repository tests."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


PAGE_WIDTH = 1800
PAGE_HEIGHT = 2600


def _font_candidates() -> list[str]:
    """Return preferred macOS Japanese font candidates for fixture rendering."""

    return [
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load the first available Japanese-capable font at the requested size."""

    for candidate in _font_candidates():
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()

def _safe_draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: int | str = "black",
) -> None:
    """Draw text with a fallback mechanism to prevent UnicodeEncodeError on default fonts."""
    try:
        draw.text(xy, text, fill=fill, font=font)
    except UnicodeEncodeError:  # pragma: no cover
        # Fallback for ImageFont.load_default() which only supports latin-1
        fallback_text = "".join(c if ord(c) < 256 else "?" for c in text)  # pragma: no cover
        draw.text(xy, fallback_text, fill=fill, font=font)  # pragma: no cover


def _draw_vertical_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    line_height: int,
) -> None:
    """Render a string as simple top-to-bottom vertical glyph placement."""

    cursor_y = y
    for char in text:
        _safe_draw_text(draw, (x, cursor_y), char, font=font)
        cursor_y += line_height


def _split_vertical(text: str, max_chars: int) -> list[str]:
    """Split text into vertical columns constrained by the page height budget."""

    return [text[idx : idx + max_chars] for idx in range(0, len(text), max_chars)]


def _draw_vertical_columns(
    draw: ImageDraw.ImageDraw,
    bbox: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    """Render multiple vertical columns of text inside the supplied bounding box."""

    x0, y0, x1, y1 = bbox
    font_size = int(getattr(font, "size", 24))
    line_height = int(font_size * 1.1)
    max_chars = max(5, (y1 - y0) // line_height)
    columns = _split_vertical(text.replace(" ", ""), max_chars)
    current_x = x1 - font_size
    step_x = int(font_size * 1.4)
    for col in columns:
        _draw_vertical_text(draw, col, current_x, y0, font, line_height)
        current_x -= step_x
        if current_x < x0:
            break


def _article_block(
    headline: str,
    body: str,
    bbox: tuple[int, int, int, int],
    vertical: bool = True,
    page_number: int = 1,
) -> dict:
    """Create one synthetic article descriptor for the fixture ground truth."""

    return {
        "headline": headline,
        "body": body,
        "bbox": list(bbox),
        "vertical": vertical,
        "page_number": page_number,
    }


def _ground_truth() -> dict:
    """Return the deterministic article/image/ad structure used for the fixture."""

    return {
        "page_size": [PAGE_WIDTH, PAGE_HEIGHT],
        "column_count": 4,
        "article_count": 4,
        "image_count": 3,
        "ad_count": 2,
        "articles": [
            _article_block(
                "次世代電池材料",
                "合成材料メーカーが量産投資を加速し、軽量太陽電池向けの供給網を整える。開発段階に応じた材料選択と高純度プロセスの両立が採用拡大の鍵となる。",
                (980, 180, 1700, 1260),
            ),
            _article_block(
                "宇宙開発を支える産業ガス",
                "液体水素、液体酸素、高圧窒素の供給体制が月探査計画の成否を左右する。極低温管理や輸送の信頼性がミッションの前提条件となる。",
                (90, 260, 900, 1450),
            ),
            _article_block(
                "生体適合性高分子",
                "抗血栓性と細胞定着性の両立を狙う新規高分子が研究用途から医療機器用途へ展開する。材料表面の水和状態制御が重要な設計因子になる。",
                (980, 1320, 1700, 2150),
            ),
            _article_block(
                "市場と政策",
                "導入目標や資源循環政策が新素材の需要形成を後押しする。企業は原料確保、品質安定、回収技術の一体戦略で差別化を図る。",
                (90, 1500, 900, 2250),
            ),
        ],
        "images": [
            {"bbox": [270, 1480, 870, 1900]},
            {"bbox": [1080, 960, 1640, 1290]},
            {"bbox": [1080, 2170, 1640, 2440]},
        ],
        "ads": [
            {"bbox": [1460, 60, 1750, 540]},
            {"bbox": [70, 2300, 1740, 2550]},
        ],
        "headline_blocks": 4,
        "vertical_article_ratio": 1.0,
        "page_count": 1,
        "headline_page_coverage": 1.0,
    }


def generate_fixture(output_dir: Path, seed: int = 7) -> tuple[Path, Path]:
    """Generate a synthetic scanned-newspaper PDF fixture and ground-truth JSON."""

    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"synthetic_newspaper_{seed}.png"
    pdf_path = output_dir / f"synthetic_newspaper_{seed}.pdf"
    truth_path = output_dir / f"synthetic_newspaper_{seed}.json"

    truth = _ground_truth()

    image = Image.new("L", (PAGE_WIDTH, PAGE_HEIGHT), color=245)
    draw = ImageDraw.Draw(image)
    headline_font = _load_font(48)
    body_font = _load_font(28)
    caption_font = _load_font(22)

    draw.rectangle((60, 40, 1740, 140), outline=0, width=3)
    _safe_draw_text(draw, (90, 65), "Synthetic Chemical Daily", font=headline_font, fill=0)

    for article in truth["articles"]:
        x0, y0, x1, y1 = article["bbox"]
        if article["vertical"]:
            _draw_vertical_columns(
                draw, (x0 + 20, y0 + 80, x1 - 20, y1 - 20), article["body"], body_font
            )
            _draw_vertical_columns(
                draw,
                (x1 - 120, y0, x1 - 20, y0 + 260),
                article["headline"],
                headline_font,
            )
        else:
            _safe_draw_text(
                draw, (x0 + 20, y0 + 20), article["headline"], font=headline_font, fill=0
            )
            _safe_draw_text(draw, (x0 + 20, y0 + 100), article["body"], font=body_font, fill=0)

    for idx, image_block in enumerate(truth["images"], start=1):
        x0, y0, x1, y1 = image_block["bbox"]
        draw.rectangle((x0, y0, x1, y1), fill=200, outline=80)
        _safe_draw_text(draw, (x0 + 20, y0 + 20), f"PHOTO {idx}", font=headline_font, fill=20)
        _safe_draw_text(
            draw, (x0 + 20, y1 - 60), f"図版キャプション {idx}", font=caption_font, fill=20
        )

    for idx, ad in enumerate(truth["ads"], start=1):
        x0, y0, x1, y1 = ad["bbox"]
        draw.rectangle((x0, y0, x1, y1), fill=225, outline=160, width=2)
        _safe_draw_text(draw, (x0 + 20, y0 + 20), f"SPONSORED {idx}", font=headline_font, fill=40)
        _safe_draw_text(
            draw, (x0 + 20, y0 + 110),
            "Synthetic industrial advertisement block.",
            font=caption_font,
            fill=40,
        )

    for x in (900, 950):
        draw.line((x, 160, x, 2260), fill=180, width=2)

    image = image.filter(ImageFilter.GaussianBlur(radius=0.6))
    image.save(image_path)

    pdf_canvas = canvas.Canvas(str(pdf_path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    with open(image_path, "rb") as img_file:
        pdf_canvas.drawImage(
            ImageReader(img_file), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT
        )
    pdf_canvas.save()

    truth_path.write_text(
        json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return pdf_path, truth_path

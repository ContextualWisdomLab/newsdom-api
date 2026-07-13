"""Build canonical NewsDOM page/article structures from parser output blocks."""

from __future__ import annotations

import re
from collections import defaultdict
from html import escape as html_escape
from itertools import count
from math import isfinite
from typing import Any

from .schemas import (
    ArticleNode,
    BoundingBox,
    CaptionNode,
    ImageNode,
    PageNode,
    ParseQuality,
    ParseResponse,
)

MAX_BBOX_COORDINATE = 1_000_000.0
MAX_CONTENT_BLOCKS = 5_000
MAX_MEDIA_PATH_LENGTH = 512
MAX_PAGE_NUMBER = 100_000
HTML_ESCAPE_PATTERN = re.compile(r"[&<>\"']")
UNSAFE_MEDIA_PATH_PATTERN = re.compile(r"[\x00-\x1f\"'<>` \t\r\n]")


def _coerce_bbox_coordinate(value: Any) -> float | None:
    """Convert a bounded, finite bounding-box coordinate into a float."""

    if isinstance(value, bool):
        return None

    try:
        coordinate = value if type(value) is float else float(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if not isfinite(coordinate):
        return None

    if coordinate < 0 or coordinate > MAX_BBOX_COORDINATE:
        return None

    return coordinate


def _bbox_from_values(values: list[Any] | None) -> BoundingBox | None:
    """Convert a four-value bounding-box list into a typed schema object."""

    if values is None:
        return None

    if len(values) != 4:
        return None

    # ⚡ Bolt: Unroll coordinate extraction to avoid generator and tuple allocation overhead.
    # This also enables early returns, stopping the function immediately if any coordinate is invalid.
    x0 = _coerce_bbox_coordinate(values[0])
    if x0 is None:
        return None

    y0 = _coerce_bbox_coordinate(values[1])
    if y0 is None:
        return None

    x1 = _coerce_bbox_coordinate(values[2])
    if x1 is None or x1 < x0:
        return None

    y1 = _coerce_bbox_coordinate(values[3])
    if y1 is None or y1 < y0:
        return None

    return BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1)


def _html_safe_text(value: Any) -> str:
    """Normalize OCR text for safe downstream HTML rendering."""
    if not value:
        return ""
    # ⚡ Bolt: Fast path for str to avoid expensive str() cast
    text = value if type(value) is str else str(value)
    text = text.strip()
    if not HTML_ESCAPE_PATTERN.search(text):
        return text
    return html_escape(text)


def _safe_media_path(value: Any, fallback: str) -> str:
    """Return a bounded relative media path or a deterministic fallback."""

    # ⚡ Bolt: Early truthiness return to avoid calling .strip() on empty strings
    if not isinstance(value, str) or not value:
        return fallback

    raw_path = value.strip()
    if not raw_path:
        return fallback

    if len(raw_path) > MAX_MEDIA_PATH_LENGTH:
        return fallback

    if raw_path.startswith("/"):
        return fallback

    if "\\" in raw_path:
        return fallback

    if ":" in raw_path:
        return fallback

    if UNSAFE_MEDIA_PATH_PATTERN.search(raw_path):
        return fallback

    for part in raw_path.split("/"):
        if part in {"", ".", ".."}:
            return fallback

    return raw_path


def _coerce_page_number(value: Any) -> int | None:
    """Convert supported page-number values into integers."""

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        page_number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if page_number < 1:
        return None

    if page_number > MAX_PAGE_NUMBER:
        return None

    return page_number


def _block_text(block: dict[str, Any]) -> str:
    """Extract normalized text from a MinerU content block."""

    return _html_safe_text(block.get("text") or block.get("contents"))


def _caption_nodes_from_items(items: Any) -> list[CaptionNode]:
    """Normalize caption-like payloads into caption nodes."""

    nodes: list[CaptionNode] = []
    if not isinstance(items, list):
        return nodes

    for item in items:
        if isinstance(item, dict):
            text = _html_safe_text(item.get("text") or item.get("contents"))
            if text:
                # ⚡ Bolt: Defer expensive bbox parsing/float casting until we actually need it
                bbox = _bbox_from_values(item.get("bbox") or item.get("box"))
                nodes.append(CaptionNode(text=text, bbox=bbox))
        else:
            text = _html_safe_text(item)
            if text:
                nodes.append(CaptionNode(text=text, bbox=None))
    return nodes


def _new_article(
    article_seq: count, headline: str, bbox: BoundingBox | None = None
) -> ArticleNode:
    """Create a new article node with the next deterministic identifier."""

    return ArticleNode(
        article_id=f"article-{next(article_seq)}",
        headline=headline,
        bbox=bbox,
    )


def _handle_media_block(
    block: dict[str, Any],
    block_type: str,
    current_article: ArticleNode | None,
    article_seq: count,
    page: PageNode,
) -> ArticleNode:
    """Extract and process media blocks into an ArticleNode."""
    bbox = _bbox_from_values(block.get("bbox") or block.get("box"))
    path = _safe_media_path(block.get("img_path") or block.get("path"), block_type)
    image = ImageNode(
        path=path,
        media_type=block_type,
        bbox=bbox,
    )
    caption_key = f"{block_type}_caption"
    footnote_key = f"{block_type}_footnote"
    image.captions.extend(_caption_nodes_from_items(block.get(caption_key)))
    image.footnotes.extend(_caption_nodes_from_items(block.get(footnote_key)))
    if current_article is None:
        current_article = _new_article(article_seq, "(untitled)")
        page.articles.append(current_article)
    current_article.images.append(image)
    return current_article


def _handle_table_block(
    block: dict[str, Any],
    current_article: ArticleNode | None,
    article_seq: count,
    page: PageNode,
) -> ArticleNode:
    """Extract and process table blocks into an ArticleNode."""
    if current_article is None:
        current_article = _new_article(article_seq, "(table-block)")
        page.articles.append(current_article)
    table_body = _html_safe_text(block.get("table_body"))
    if table_body:
        current_article.body_blocks.append(table_body)
    current_article.captions.extend(
        _caption_nodes_from_items(block.get("table_caption"))
    )
    current_article.footnotes.extend(
        _caption_nodes_from_items(block.get("table_footnote"))
    )
    return current_article


def _handle_text_block(
    block: dict[str, Any],
    text: str,
    role: Any,
    current_article: ArticleNode | None,
    article_seq: count,
    page: PageNode,
) -> ArticleNode:
    """Extract and process text and headline blocks into an ArticleNode."""
    text_level = block.get("text_level")
    is_headline = (text_level == 1) or (role == "section_headings")
    clean_text = text.replace("\n", " ") if "\n" in text else text
    if is_headline:
        bbox = _bbox_from_values(block.get("bbox") or block.get("box"))
        current_article = _new_article(article_seq, clean_text, bbox)
        page.articles.append(current_article)
        return current_article

    if current_article is None:
        current_article = _new_article(article_seq, "(untitled)")
        page.articles.append(current_article)
    current_article.body_blocks.append(clean_text)
    return current_article


def _build_page_dom(
    content_list: list[dict[str, Any]],
    *,
    page_number: int,
    article_seq: count,
    width: float | None = None,
    height: float | None = None,
) -> PageNode:
    """Normalize MinerU-style content blocks into a canonical NewsDOM page."""

    page = PageNode(page_number=page_number, width=width, height=height)
    current_article: ArticleNode | None = None

    for block in content_list:
        block_type = block.get("type")
        role = block.get("role")

        if role == "header":
            # ⚡ Bolt: Defer expensive string operations until we know we need the text
            text = _block_text(block)
            if text:
                page.headers.append(text)
            continue

        if role == "footer":
            text = _block_text(block)
            if text:
                page.footers.append(text)
            continue

        if role == "page_number":
            text = _block_text(block)
            if text:
                page.page_numbers.append(text)
            continue

        if role == "ad" or block_type == "ad":
            text = _block_text(block)
            if text:
                page.ads.append(text)
            continue

        if block_type in {"image", "chart"}:
            current_article = _handle_media_block(
                block, block_type, current_article, article_seq, page
            )
            continue

        if block_type == "table":
            current_article = _handle_table_block(
                block, current_article, article_seq, page
            )
            continue

        text = _block_text(block)
        if not text:
            continue

        current_article = _handle_text_block(
            block, text, role, current_article, article_seq, page
        )

    return page


def _page_number_from_info(page_info: dict[str, Any], fallback: int) -> int:
    """Resolve page numbering from MinerU page metadata."""

    page_number = page_info.get("page_number")
    if isinstance(page_number, bool):
        page_number = None

    if isinstance(page_number, int):
        normalized_page_number = _coerce_page_number(page_number)
        if normalized_page_number is not None:
            return normalized_page_number

    page_no = page_info.get("page_no")
    if isinstance(page_no, bool):
        page_no = None

    if isinstance(page_no, int):
        normalized_page_no = _coerce_page_number(page_no + 1)
        if normalized_page_no is not None:
            return normalized_page_no

    return fallback


def _extract_page_info_by_idx(
    model: list[dict[str, Any]] | None,
) -> dict[int, dict[str, Any]]:
    """Extract page information from the model payload by index."""
    page_info_by_idx: dict[int, dict[str, Any]] = {}
    if model:
        for index, page_model in enumerate(model):
            page_info = page_model.get("page_info") or {}
            page_info_by_idx[index] = page_info
    return page_info_by_idx


def _group_blocks_by_page_idx(
    content_list: list[dict[str, Any]],
) -> tuple[bool, bool, dict[int, list[dict[str, Any]]]]:
    """Group content blocks by their page index."""
    has_page_idx = False
    has_missing_page_idx = False
    # ⚡ Bolt: Use defaultdict instead of dict.setdefault in this hot grouping loop
    # to avoid the overhead of instantiating an empty list on every single iteration
    blocks_by_page_idx: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)

    for block in content_list:
        raw_page_idx = block.get("page_idx")
        if isinstance(raw_page_idx, int):
            has_page_idx = True
            normalized_page_idx = raw_page_idx
        else:
            has_missing_page_idx = True
            normalized_page_idx = 0
        blocks_by_page_idx[normalized_page_idx].append(block)

    return has_page_idx, has_missing_page_idx, blocks_by_page_idx


def _build_pages_without_page_idx(
    content_list: list[dict[str, Any]],
    page_info_by_idx: dict[int, dict[str, Any]],
    quality_warnings: list[str],
) -> list[PageNode]:
    """Build pages when no blocks have a page_idx."""
    article_seq = count(1)
    if len(page_info_by_idx) > 1:
        quality_warnings.append(
            "Some blocks are missing page_idx; content was assigned to page_idx 0 while preserving model-declared page count."
        )
        pages = []
        for page_idx in sorted(page_info_by_idx):
            page_info = page_info_by_idx.get(page_idx, {})
            pages.append(
                _build_page_dom(
                    content_list if page_idx == 0 else [],
                    page_number=_page_number_from_info(page_info, page_idx + 1),
                    article_seq=article_seq,
                    width=page_info.get("width"),
                    height=page_info.get("height"),
                )
            )
        return pages

    page_info = page_info_by_idx.get(0, {})
    return [
        _build_page_dom(
            content_list,
            page_number=_page_number_from_info(page_info, 1),
            article_seq=article_seq,
            width=page_info.get("width"),
            height=page_info.get("height"),
        )
    ]


def _build_pages_with_page_idx(
    blocks_by_page_idx: dict[int, list[dict[str, Any]]],
    page_info_by_idx: dict[int, dict[str, Any]],
    has_missing_page_idx: bool,
    quality_warnings: list[str],
) -> list[PageNode]:
    """Build pages when at least some blocks have a page_idx."""
    if has_missing_page_idx and len(page_info_by_idx) > 1:
        quality_warnings.append(
            "Some blocks are missing page_idx; untagged blocks were assigned to page_idx 0 for deterministic grouping."
        )

    pages = []
    article_seq = count(1)
    for page_idx in sorted(blocks_by_page_idx):
        page_info = page_info_by_idx.get(page_idx, {})
        pages.append(
            _build_page_dom(
                blocks_by_page_idx[page_idx],
                page_number=_page_number_from_info(page_info, page_idx + 1),
                article_seq=article_seq,
                width=page_info.get("width"),
                height=page_info.get("height"),
            )
        )
    return pages


def build_dom(
    content_list: list[dict[str, Any]],
    document_id: str,
    model: list[dict[str, Any]] | None = None,
) -> ParseResponse:
    """Normalize MinerU-style content blocks into the canonical NewsDOM schema."""

    if not isinstance(content_list, list):
        raise ValueError("content_list must be a list of MinerU content blocks")

    if len(content_list) > MAX_CONTENT_BLOCKS:
        raise ValueError(
            f"content_list contains more than {MAX_CONTENT_BLOCKS} content blocks"
        )

    page_info_by_idx = _extract_page_info_by_idx(model)
    quality_warnings: list[str] = []

    has_page_idx, has_missing_page_idx, blocks_by_page_idx = _group_blocks_by_page_idx(
        content_list
    )

    if not has_page_idx:
        pages = _build_pages_without_page_idx(
            content_list, page_info_by_idx, quality_warnings
        )
    else:
        pages = _build_pages_with_page_idx(
            blocks_by_page_idx,
            page_info_by_idx,
            has_missing_page_idx,
            quality_warnings,
        )

    return ParseResponse(
        document_id=document_id,
        pages=pages,
        quality=ParseQuality(warnings=quality_warnings),
    )

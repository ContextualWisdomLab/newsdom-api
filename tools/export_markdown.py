from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _format_bbox(bbox: Any) -> str:
    if isinstance(bbox, dict):
        x0 = bbox.get("x0")
        y0 = bbox.get("y0")
        x1 = bbox.get("x1")
        y1 = bbox.get("y1")
        if x0 is not None and y0 is not None and x1 is not None and y1 is not None:
            return f"(x0: {x0}, y0: {y0}, x1: {x1}, y1: {y1})"
    return ""


def _caption_text(caption: Any) -> str:

    if isinstance(caption, dict):
        return str(caption.get("text", ""))
    return str(caption)


def generate_markdown(data: dict[str, Any]) -> str:
    """Convert a NewsDOM JSON dictionary into Markdown."""
    lines: list[str] = []

    document_id = data.get("document_id", "Unknown Document")
    lines.extend([f"# Document: {document_id}", ""])

    quality = data.get("quality")
    if isinstance(quality, dict):
        status = quality.get("status", "unknown")
        parser = quality.get("parser", "unknown")
        lines.append(f"**Parse Status**: {status} (Parser: {parser})")
        warnings = quality.get("warnings", [])
        if warnings:
            lines.append("**Warnings**:")
            for w in warnings:
                lines.append(f"- {w}")
        lines.append("")

    for page in data.get("pages", []):
        if not isinstance(page, dict):
            continue

        page_number = page.get("page_number", "Unknown")
        lines.extend([f"## Page {page_number}", ""])

        width = page.get("width")
        height = page.get("height")
        if width is not None and height is not None:
            lines.extend([f"**Dimensions**: {width} x {height}", ""])

        headers = page.get("headers", [])
        if headers:
            lines.append("### Headers")
            lines.extend(f"- {header}" for header in headers)
            lines.append("")

        for article in page.get("articles", []):
            if not isinstance(article, dict):
                continue

            headline = article.get("headline", "Untitled Article")
            lines.extend([f"### Article: {headline}", ""])

            bbox = article.get("bbox")
            if bbox:
                bbox_str = _format_bbox(bbox)
                if bbox_str:
                    lines.extend([f"**Bounding Box**: {bbox_str}", ""])

            for block in article.get("body_blocks", []):
                lines.extend([str(block), ""])

            for index, image in enumerate(article.get("images", []), 1):
                if not isinstance(image, dict):
                    continue
                path = image.get("path", "")
                media_type = image.get("media_type", "image")

                img_desc = f"**Image {index}**: `{path}` (Type: {media_type})"
                bbox = image.get("bbox")
                if bbox:
                    bbox_str = _format_bbox(bbox)
                    if bbox_str:
                        img_desc += f" [BBox: {bbox_str}]"
                lines.append(img_desc)

                for caption in image.get("captions", []):
                    cap_text = _caption_text(caption)
                    cap_line = f"  - Caption: {cap_text}"
                    if isinstance(caption, dict):
                        cap_bbox = caption.get("bbox")
                        if cap_bbox:
                            cap_bbox_str = _format_bbox(cap_bbox)
                            if cap_bbox_str:
                                cap_line += f" [BBox: {cap_bbox_str}]"
                    lines.append(cap_line)
                lines.append("")

            captions = article.get("captions", [])
            if captions:
                for caption in captions:  # pragma: no branch
                    cap_text = _caption_text(caption)
                    cap_line = f"- Caption: {cap_text}"
                    if isinstance(caption, dict):
                        cap_bbox = caption.get("bbox")
                        if cap_bbox:
                            cap_bbox_str = _format_bbox(cap_bbox)
                            if cap_bbox_str:
                                cap_line += f" [BBox: {cap_bbox_str}]"
                    lines.append(cap_line)
                lines.append("")

            footnotes = article.get("footnotes", [])
            if footnotes:
                lines.extend(
                    f"- Footnote: {_caption_text(footnote)}" for footnote in footnotes
                )
                lines.append("")

        ads = page.get("ads", [])
        if ads:
            lines.append("### Advertisements")
            lines.extend(f"- {ad}" for ad in ads)
            lines.append("")

        footers = page.get("footers", [])
        if footers:
            lines.append("### Footers")
            lines.extend(f"- {footer}" for footer in footers)
            lines.append("")

        page_numbers = page.get("page_numbers", [])
        if page_numbers:
            lines.append("### Page Numbers")
            lines.extend(f"- {page_number}" for page_number in page_numbers)
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-Markdown export CLI."""
    parser = argparse.ArgumentParser(
        description="Export a NewsDOM JSON file to Markdown."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to write Markdown output. Defaults to stdout.",
    )

    args = parser.parse_args(argv)

    try:
        input_data = json.loads(args.input.read_text(encoding="utf-8"))
        markdown_content = generate_markdown(input_data)
        if args.output is None:
            print(markdown_content, end="")
        else:
            args.output.write_text(markdown_content, encoding="utf-8")
            print(f"Markdown written to {args.output}")
    except Exception as exc:
        print(f"Error exporting Markdown: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

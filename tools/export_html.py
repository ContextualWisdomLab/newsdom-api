from __future__ import annotations

import argparse
import html
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
        return html.escape(str(caption.get("text", "")))
    return html.escape(str(caption))


def generate_html(data: dict[str, Any]) -> str:
    """Convert a NewsDOM JSON dictionary into an HTML string."""
    document_id = html.escape(data.get("document_id", "Unknown Document"))

    css = """
        body { font-family: sans-serif; margin: 2rem; background: #f9f9f9; color: #333; }
        .page { background: #fff; border: 1px solid #ccc; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .page-header { border-bottom: 2px solid #eee; margin-bottom: 1rem; padding-bottom: 0.5rem; }
        .article { margin-bottom: 2rem; }
        .article-headline { color: #2c3e50; }
        .body-block { line-height: 1.6; margin-bottom: 1rem; }
        .image-container { margin: 1rem 0; padding: 1rem; background: #f0f0f0; border-radius: 4px; }
        .caption { font-size: 0.9em; color: #666; font-style: italic; }
        .footnote { font-size: 0.85em; color: #777; border-top: 1px solid #eee; padding-top: 0.5rem; margin-top: 1rem; }
        .ad-block { background: #ffeaa7; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #fdcb6e; }
        .footer-block { font-size: 0.8em; text-align: center; color: #999; border-top: 1px solid #eee; padding-top: 1rem; margin-top: 2rem; }
        .quality-block { background: #e8f4f8; padding: 1rem; margin-bottom: 2rem; border-radius: 4px; }
        .bbox { font-size: 0.85em; color: #888; font-family: monospace; }
        .media-type { font-size: 0.85em; background: #eee; padding: 0.2rem 0.4rem; border-radius: 3px; }
        .dimensions { font-size: 0.9em; color: #555; margin-bottom: 1rem; }
    """

    lines: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        f"<title>{document_id}</title>",
        f"<style>{css}</style>",
        "</head>",
        "<body>",
        f"<h1>Document: {document_id}</h1>",
    ]

    quality = data.get("quality")
    if isinstance(quality, dict):
        status = html.escape(str(quality.get("status", "unknown")))
        parser = html.escape(str(quality.get("parser", "unknown")))
        lines.append('<div class="quality-block">')
        lines.append(
            f"<div><strong>Parse Status:</strong> {status} (Parser: {parser})</div>"
        )
        warnings = quality.get("warnings", [])
        if warnings:
            lines.append("<div><strong>Warnings:</strong><ul>")
            for w in warnings:
                lines.append(f"<li>{html.escape(str(w))}</li>")
            lines.append("</ul></div>")
        lines.append("</div>")

    for page in data.get("pages", []):
        if not isinstance(page, dict):
            continue

        page_number = html.escape(str(page.get("page_number", "Unknown")))
        lines.append('<div class="page">')
        lines.append(f'<div class="page-header"><h2>Page {page_number}</h2></div>')

        width = page.get("width")
        height = page.get("height")
        if width is not None and height is not None:
            lines.append(
                f'<div class="dimensions">Dimensions: {width} x {height}</div>'
            )

        headers = page.get("headers", [])
        if headers:
            lines.append('<div class="headers">')
            for header in headers:  # pragma: no branch
                lines.append(
                    f"<div><strong>Header:</strong> {html.escape(str(header))}</div>"
                )
            lines.append("</div><hr>")

        for article in page.get("articles", []):
            if not isinstance(article, dict):
                continue

            headline = html.escape(str(article.get("headline", "Untitled Article")))
            lines.append('<div class="article">')
            lines.append(f'<h3 class="article-headline">{headline}</h3>')

            bbox = article.get("bbox")
            if bbox:
                bbox_str = html.escape(_format_bbox(bbox))
                if bbox_str:
                    lines.append(f'<div class="bbox">Bounding Box: {bbox_str}</div>')

            for block in article.get("body_blocks", []):
                lines.append(f'<p class="body-block">{html.escape(str(block))}</p>')

            for index, image in enumerate(article.get("images", []), 1):
                if not isinstance(image, dict):
                    continue
                path = html.escape(str(image.get("path", "")))
                media_type = html.escape(str(image.get("media_type", "image")))
                lines.append('<div class="image-container">')

                img_desc = f'<strong>Image {index}:</strong> <code>{path}</code> <span class="media-type">{media_type}</span>'
                bbox = image.get("bbox")
                if bbox:
                    bbox_str = html.escape(_format_bbox(bbox))
                    if bbox_str:
                        img_desc += f' <span class="bbox">[BBox: {bbox_str}]</span>'
                lines.append(f"<div>{img_desc}</div>")

                for caption in image.get("captions", []):
                    cap_text = _caption_text(caption)
                    cap_line = f"Caption: {cap_text}"
                    if isinstance(caption, dict):
                        cap_bbox = caption.get("bbox")
                        if cap_bbox:
                            cap_bbox_str = html.escape(_format_bbox(cap_bbox))
                            if cap_bbox_str:
                                cap_line += (
                                    f' <span class="bbox">[BBox: {cap_bbox_str}]</span>'
                                )
                    lines.append(f'<div class="caption">{cap_line}</div>')
                lines.append("</div>")

            captions = article.get("captions", [])
            if captions:
                lines.append('<div class="captions">')
                for caption in captions:  # pragma: no branch
                    cap_text = _caption_text(caption)
                    cap_line = f"Caption: {cap_text}"
                    if isinstance(caption, dict):
                        cap_bbox = caption.get("bbox")
                        if cap_bbox:
                            cap_bbox_str = html.escape(_format_bbox(cap_bbox))
                            if cap_bbox_str:
                                cap_line += (
                                    f' <span class="bbox">[BBox: {cap_bbox_str}]</span>'
                                )
                    lines.append(f'<div class="caption">{cap_line}</div>')
                lines.append("</div>")

            footnotes = article.get("footnotes", [])
            if footnotes:
                lines.append('<div class="footnotes">')
                for footnote in footnotes:
                    lines.append(
                        f'<div class="footnote">Footnote: {_caption_text(footnote)}</div>'
                    )
                lines.append("</div>")

            lines.append("</div>")  # close article

        ads = page.get("ads", [])
        if ads:
            lines.append('<div class="ads">')
            for ad in ads:
                lines.append(f'<div class="ad-block">{html.escape(str(ad))}</div>')
            lines.append("</div>")

        footers = page.get("footers", [])
        if footers:
            lines.append('<div class="footer-block">')
            for footer in footers:
                lines.append(f"<div>{html.escape(str(footer))}</div>")
            lines.append("</div>")

        page_numbers = page.get("page_numbers", [])
        if page_numbers:
            lines.append(
                '<div class="page-numbers" style="text-align: right; margin-top: 1rem;">'
            )
            for pnum in page_numbers:
                lines.append(f"<span>Page No: {html.escape(str(pnum))}</span> ")
            lines.append("</div>")

        lines.append("</div>")  # close page

    lines.extend(["</body>", "</html>", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-HTML export CLI."""
    parser = argparse.ArgumentParser(description="Export a NewsDOM JSON file to HTML.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to write HTML output. Defaults to stdout.",
    )

    args = parser.parse_args(argv)

    try:
        input_data = json.loads(args.input.read_text(encoding="utf-8"))
        html_content = generate_html(input_data)
        if args.output is None:
            print(html_content, end="")
        else:
            args.output.write_text(html_content, encoding="utf-8")
            print(f"HTML written to {args.output}")
    except Exception as exc:
        print(f"Error exporting HTML: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

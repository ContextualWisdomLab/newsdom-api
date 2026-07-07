from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any


def _caption_text(caption: Any) -> str:
    if isinstance(caption, dict):
        return str(caption.get("text", ""))
    return str(caption)


def generate_html(data: dict[str, Any]) -> str:
    """Convert a NewsDOM JSON dictionary into HTML."""
    lines: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="ja">',
        "<head>",
        '<meta charset="UTF-8">',
        "<title>NewsDOM Export</title>",
        "<style>",
        "body { font-family: sans-serif; margin: 2rem; }",
        ".page { border: 1px solid #ccc; padding: 1rem; margin-bottom: 2rem; }",
        ".article { border: 1px solid #eee; padding: 1rem; margin-bottom: 1rem; }",
        "img { max-width: 100%; height: auto; }",
        "</style>",
        "</head>",
        "<body>",
    ]

    document_id = data.get("document_id", "Unknown Document")
    lines.append(f"<h1>Document: {html.escape(str(document_id))}</h1>")

    for page in data.get("pages", []):
        if not isinstance(page, dict):
            continue

        page_number = page.get("page_number", "Unknown")
        lines.append('<div class="page">')
        lines.append(f"<h2>Page {html.escape(str(page_number))}</h2>")

        headers = page.get("headers", [])
        if headers:
            lines.append("<h3>Headers</h3><ul>")
            lines.extend(f"<li>{html.escape(str(header))}</li>" for header in headers)
            lines.append("</ul>")

        for article in page.get("articles", []):
            if not isinstance(article, dict):
                continue

            headline = article.get("headline", "Untitled Article")
            lines.append('<div class="article">')
            lines.append(f"<h3>Article: {html.escape(str(headline))}</h3>")

            for block in article.get("body_blocks", []):
                lines.append(f"<p>{html.escape(str(block))}</p>")

            for index, image in enumerate(article.get("images", []), 1):
                if not isinstance(image, dict):
                    continue
                path = image.get("path", "")
                lines.append(
                    f"<div><strong>Image {index}</strong>: <code>{html.escape(str(path))}</code></div>"
                )
                lines.append("<ul>")
                for caption in image.get("captions", []):
                    lines.append(
                        f"<li>Caption: {html.escape(_caption_text(caption))}</li>"
                    )
                lines.append("</ul>")

            captions = article.get("captions", [])
            if captions:
                lines.append("<ul>")
                lines.extend(
                    f"<li>Caption: {html.escape(_caption_text(caption))}</li>"
                    for caption in captions
                )
                lines.append("</ul>")

            footnotes = article.get("footnotes", [])
            if footnotes:
                lines.append("<ul>")
                lines.extend(
                    f"<li>Footnote: {html.escape(_caption_text(footnote))}</li>"
                    for footnote in footnotes
                )
                lines.append("</ul>")

            lines.append("</div>")  # End article

        ads = page.get("ads", [])
        if ads:
            lines.append("<h3>Advertisements</h3><ul>")
            lines.extend(f"<li>{html.escape(str(ad))}</li>" for ad in ads)
            lines.append("</ul>")

        footers = page.get("footers", [])
        if footers:
            lines.append("<h3>Footers</h3><ul>")
            lines.extend(f"<li>{html.escape(str(footer))}</li>" for footer in footers)
            lines.append("</ul>")

        page_numbers = page.get("page_numbers", [])
        if page_numbers:
            lines.append("<h3>Page Numbers</h3><ul>")
            lines.extend(
                f"<li>{html.escape(str(page_number))}</li>"
                for page_number in page_numbers
            )
            lines.append("</ul>")

        lines.append("</div>")  # End page

    lines.append("</body>")
    lines.append("</html>")
    return "\n".join(lines) + "\n"


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
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: Invalid JSON - {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error exporting HTML: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

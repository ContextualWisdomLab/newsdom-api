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
        "article { border-bottom: 1px solid #ccc; padding-bottom: 1rem; margin-bottom: 1rem; }",
        "img { max-width: 100%; height: auto; }",
        "</style>",
        "</head>",
        "<body>",
    ]

    document_id = html.escape(data.get("document_id", "Unknown Document"))
    lines.append(f"<h1>Document: {document_id}</h1>")

    for page in data.get("pages", []):
        if not isinstance(page, dict):
            continue

        page_number = page.get("page_number", "Unknown")
        lines.append('<section class="page">')
        lines.append(f"<h2>Page {html.escape(str(page_number))}</h2>")

        headers = page.get("headers", [])
        if headers:
            lines.append('<div class="headers">')
            lines.append("<h3>Headers</h3>")
            lines.append("<ul>")
            lines.extend(f"<li>{html.escape(str(header))}</li>" for header in headers)
            lines.append("</ul>")
            lines.append("</div>")

        for article in page.get("articles", []):
            if not isinstance(article, dict):
                continue

            headline = html.escape(article.get("headline", "Untitled Article"))
            lines.append("<article>")
            lines.append(f"<h3>Article: {headline}</h3>")

            for block in article.get("body_blocks", []):
                lines.append(f"<p>{html.escape(str(block))}</p>")

            for index, image in enumerate(article.get("images", []), 1):
                if not isinstance(image, dict):
                    continue
                path = html.escape(image.get("path", ""))
                lines.append("<figure>")
                lines.append(f'<img src="{path}" alt="Image {index}">')
                for caption in image.get("captions", []):
                    lines.append(
                        f"<figcaption>Caption: {html.escape(_caption_text(caption))}</figcaption>"
                    )
                lines.append("</figure>")

            captions = article.get("captions", [])
            if captions:
                lines.append('<div class="captions">')
                lines.extend(
                    f"<p>Caption: {html.escape(_caption_text(caption))}</p>"
                    for caption in captions
                )
                lines.append("</div>")

            footnotes = article.get("footnotes", [])
            if footnotes:
                lines.append('<div class="footnotes">')
                lines.extend(
                    f"<p>Footnote: {html.escape(_caption_text(footnote))}</p>"
                    for footnote in footnotes
                )
                lines.append("</div>")

            lines.append("</article>")

        ads = page.get("ads", [])
        if ads:
            lines.append('<div class="ads">')
            lines.append("<h3>Advertisements</h3>")
            lines.append("<ul>")
            lines.extend(f"<li>{html.escape(str(ad))}</li>" for ad in ads)
            lines.append("</ul>")
            lines.append("</div>")

        footers = page.get("footers", [])
        if footers:
            lines.append('<div class="footers">')
            lines.append("<h3>Footers</h3>")
            lines.append("<ul>")
            lines.extend(f"<li>{html.escape(str(footer))}</li>" for footer in footers)
            lines.append("</ul>")
            lines.append("</div>")

        page_numbers = page.get("page_numbers", [])
        if page_numbers:
            lines.append('<div class="page-numbers">')
            lines.append("<h3>Page Numbers</h3>")
            lines.append("<ul>")
            lines.extend(
                f"<li>{html.escape(str(page_number))}</li>"
                for page_number in page_numbers
            )
            lines.append("</ul>")
            lines.append("</div>")

        lines.append("</section>")

    lines.extend(["</body>", "</html>"])
    return "\n".join(lines).strip() + "\n"


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

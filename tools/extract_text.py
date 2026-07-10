from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _extract_text_from_node(node: dict | str | None) -> str:
    """Helper to safely extract text from a node that could be a dict or string."""
    if node is None:
        return ""
    if isinstance(node, dict):
        return str(node.get("text", ""))
    return str(node)


def extract_plain_text(data: dict) -> str:
    """Extract plain text from NewsDOM JSON data."""
    text_blocks: list[str] = []

    pages = data.get("pages", [])
    if not isinstance(pages, list):
        return ""

    for page in pages:
        if not isinstance(page, dict):
            continue

        # Headers
        for header in page.get("headers", []):
            if header:
                text_blocks.append(str(header))

        # Articles
        for article in page.get("articles", []):
            if not isinstance(article, dict):
                continue

            headline = article.get("headline")
            if headline:
                text_blocks.append(str(headline))

            for block in article.get("body_blocks", []):
                if block:
                    text_blocks.append(str(block))

            # Image captions/footnotes inside articles
            for image in article.get("images", []):
                if not isinstance(image, dict):
                    continue
                for caption in image.get("captions", []):
                    cap_text = _extract_text_from_node(caption)
                    if cap_text:
                        text_blocks.append(cap_text)

            # Captions at article level
            for caption in article.get("captions", []):
                cap_text = _extract_text_from_node(caption)
                if cap_text:
                    text_blocks.append(cap_text)

            # Footnotes at article level
            for footnote in article.get("footnotes", []):
                fn_text = _extract_text_from_node(footnote)
                if fn_text:
                    text_blocks.append(fn_text)

        # Ads
        for ad in page.get("ads", []):
            if ad:
                text_blocks.append(str(ad))

        # Footers
        for footer in page.get("footers", []):
            if footer:
                text_blocks.append(str(footer))

    return "\n".join(text_blocks)


def main(argv: list[str] | None = None) -> None:
    """Run the plain text extraction CLI."""
    parser = argparse.ArgumentParser(
        description="Extract all readable text from a NewsDOM JSON file into a plain text string."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to write the extracted text. Defaults to stdout.",
    )

    args = parser.parse_args(argv)

    try:
        input_path = args.input
        if not input_path.is_file():
            raise FileNotFoundError(f"File not found or is not a file: {input_path}")
        if input_path.suffix.lower() != ".json":
            raise ValueError("Input file must be a .json file.")

        data = json.loads(input_path.read_text(encoding="utf-8"))
        extracted_text = extract_plain_text(data)

        if args.output:
            args.output.write_text(extracted_text, encoding="utf-8")
            print(f"Extracted text written to {args.output}")
        else:
            print(extracted_text, end="")

    except Exception as e:
        print(f"Error extracting text: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _caption_text(caption: Any) -> str:
    if isinstance(caption, dict):
        return str(caption.get("text", ""))
    return str(caption)


def extract_plain_text(data: dict[str, Any]) -> str:
    """Extract purely plain text from a NewsDOM JSON dictionary."""
    texts: list[str] = []

    for page in data.get("pages", []):
        if not isinstance(page, dict):
            continue

        headers = page.get("headers", [])
        if headers:
            texts.extend(str(h) for h in headers if h)

        for article in page.get("articles", []):
            if not isinstance(article, dict):
                continue

            headline = article.get("headline", "")
            if headline:
                texts.append(str(headline))

            for block in article.get("body_blocks", []):
                if block:
                    texts.append(str(block))

            for image in article.get("images", []):
                if not isinstance(image, dict):
                    continue
                for caption in image.get("captions", []):
                    c_text = _caption_text(caption)
                    if c_text:
                        texts.append(c_text)
                for footnote in image.get("footnotes", []):
                    f_text = _caption_text(footnote)
                    if f_text:
                        texts.append(f_text)

            captions = article.get("captions", [])
            if captions:
                for caption in captions:
                    c_text = _caption_text(caption)
                    if c_text:
                        texts.append(c_text)

            footnotes = article.get("footnotes", [])
            if footnotes:
                for footnote in footnotes:
                    f_text = _caption_text(footnote)
                    if f_text:
                        texts.append(f_text)

        ads = page.get("ads", [])
        if ads:
            texts.extend(str(a) for a in ads if a)

        footers = page.get("footers", [])
        if footers:
            texts.extend(str(f) for f in footers if f)

    # Filter out any lingering empty strings and join with double newlines
    clean_texts = [t.strip() for t in texts if t.strip()]
    return "\n\n".join(clean_texts) + "\n" if clean_texts else ""


def main(argv: list[str] | None = None) -> None:
    """Run the plain text extraction CLI."""
    parser = argparse.ArgumentParser(
        description="Extract plain text from a NewsDOM JSON file."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to write text output. Defaults to stdout.",
    )

    args = parser.parse_args(argv)

    try:
        input_data = json.loads(args.input.read_text(encoding="utf-8"))
        plain_text = extract_plain_text(input_data)
        if args.output is None:
            print(plain_text, end="")
        else:
            args.output.write_text(plain_text, encoding="utf-8")
            print(f"Text extracted and written to {args.output}")
    except Exception as exc:
        print(f"Error extracting text: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

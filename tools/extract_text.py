from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def extract_text(json_path: Path) -> str:
    """Extract text from NewsDOM JSON."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    data = json.loads(json_path.read_bytes())
    pages = data.get("pages", [])

    extracted_texts = []

    for page in pages:
        for header in page.get("headers", []):
            extracted_texts.append(header)

        for article in page.get("articles", []):
            headline = article.get("headline", "")
            if headline:
                extracted_texts.append(headline)

            for block in article.get("body_blocks", []):
                extracted_texts.append(block)

            for caption in article.get("captions", []):
                if isinstance(caption, dict) and "text" in caption:
                    extracted_texts.append(caption["text"])

            for footnote in article.get("footnotes", []):
                if isinstance(footnote, dict) and "text" in footnote:
                    extracted_texts.append(footnote["text"])

            for image in article.get("images", []):
                for caption in image.get("captions", []):
                    if isinstance(caption, dict) and "text" in caption:
                        extracted_texts.append(caption["text"])
                for footnote in image.get("footnotes", []):
                    if isinstance(footnote, dict) and "text" in footnote:
                        extracted_texts.append(footnote["text"])

        for ad in page.get("ads", []):
            extracted_texts.append(ad)

        for footer in page.get("footers", []):
            extracted_texts.append(footer)

    return "\n".join(extracted_texts)


def main(argv: list[str] | None = None) -> None:
    """Run extract_text main entry point."""
    parser = argparse.ArgumentParser(description="Extract text from NewsDOM JSON.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to save the extracted text.",
        default=None,
    )

    args = parser.parse_args(argv)

    try:
        text = extract_text(args.input)
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

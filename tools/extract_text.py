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

    data = json.loads(json_path.read_text(encoding="utf-8"))

    extracted = []

    document_id = data.get("document_id", "")
    if document_id:
        extracted.append(f"Document: {document_id}")
        extracted.append("")

    for page in data.get("pages", []):
        if not isinstance(page, dict):
            continue

        page_number = page.get("page_number", "")
        if page_number is not None and str(page_number).strip() != "":
            extracted.append(f"--- Page {page_number} ---")
            extracted.append("")

        for header in page.get("headers", []):
            extracted.append(str(header))
            extracted.append("")

        for article in page.get("articles", []):
            if not isinstance(article, dict):
                continue

            headline = article.get("headline", "")
            if headline:
                extracted.append(str(headline))
                extracted.append("")

            for block in article.get("body_blocks", []):
                extracted.append(str(block))
                extracted.append("")

        for footer in page.get("footers", []):
            extracted.append(str(footer))
            extracted.append("")

    return "\n".join(extracted).strip() + "\n" if extracted else ""


def main(argv: list[str] | None = None) -> None:
    """Run the JSON text extraction CLI."""
    parser = argparse.ArgumentParser(
        description="Extract raw text from a NewsDOM JSON file."
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
        text_content = extract_text(args.input)
        if args.output is None:
            print(text_content, end="")
        else:
            args.output.write_text(text_content, encoding="utf-8")
            print(f"Text written to {args.output}")
    except Exception as exc:
        print(f"Error extracting text: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def extract_text(json_path: Path, output_path: Path | None = None) -> None:
    """Extract headline and body blocks text from parsed DOM JSON."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    extracted_lines = []

    pages = data.get("pages", [])
    for page in pages:
        articles = page.get("articles", [])
        for article in articles:
            headline = article.get("headline", "")
            if headline:
                extracted_lines.append(f"# {headline}")
                extracted_lines.append("")

            body_blocks = article.get("body_blocks", [])
            for block in body_blocks:
                extracted_lines.append(block)
                extracted_lines.append("")

            extracted_lines.append("---")
            extracted_lines.append("")

    extracted_text = "\n".join(extracted_lines)

    if output_path:
        output_path.write_text(extracted_text, encoding="utf-8")
        print(f"Extracted text saved to {output_path}")
    else:
        print(extracted_text)


def main(argv: list[str] | None = None) -> None:
    """Run extract_text main entry point."""
    parser = argparse.ArgumentParser(description="Extract text from NewsDOM JSON.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to save the extracted text. If omitted, prints to stdout.",
    )

    args = parser.parse_args(argv)

    try:
        extract_text(args.input, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

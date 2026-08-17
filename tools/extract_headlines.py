from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_document(json_path: Path) -> dict[str, Any]:
    """Load one NewsDOM JSON object from an existing `.json` file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("NewsDOM JSON root must be an object.")
    return data


def extract_headlines(json_path: Path) -> list[str]:
    """Extract non-empty headline strings in document order from NewsDOM JSON."""
    data = _load_document(json_path)
    pages = data.get("pages", [])
    if not isinstance(pages, list):
        raise ValueError("NewsDOM pages must be a list.")

    headlines: list[str] = []
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("NewsDOM pages must contain objects.")
        articles = page.get("articles", [])
        if not isinstance(articles, list):
            raise ValueError("NewsDOM article collections must be lists.")
        for article in articles:
            if not isinstance(article, dict):
                raise ValueError("NewsDOM articles must contain objects.")
            headline = article.get("headline")
            if headline is None:
                continue
            if not isinstance(headline, str):
                raise ValueError("NewsDOM headline values must be strings when present.")
            if headline:
                headlines.append(headline)
    return headlines


def main(argv: list[str] | None = None) -> None:
    """Run the headline-extraction command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Extract headlines from NewsDOM JSON output in document order."
    )
    parser.add_argument("input", type=Path, help="Path to the NewsDOM JSON file.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path for newline-delimited extracted headlines.",
    )
    args = parser.parse_args(argv)

    try:
        headlines = extract_headlines(args.input)
        if args.output is not None:
            output_text = "\n".join(headlines)
            if headlines:
                output_text += "\n"
            args.output.write_text(output_text, encoding="utf-8")
            print(f"Extracted {len(headlines)} headlines to {args.output}")
        else:
            for headline in headlines:
                print(headline)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":  # pragma: no cover
    main()

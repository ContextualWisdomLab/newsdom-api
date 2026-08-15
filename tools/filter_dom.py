from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def filter_dom(json_path: Path, query: str, out_path: Path) -> None:
    """Filter DOM JSON retaining only articles matching the text query."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    for page in pages:
        filtered_articles = []
        for article in page.get("articles", []):
            headline = article.get("headline", "")
            if pattern.search(headline):
                filtered_articles.append(article)
                continue

            body_blocks = article.get("body_blocks", [])
            if any(pattern.search(block) for block in body_blocks):
                filtered_articles.append(article)

        page["articles"] = filtered_articles

    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter NewsDOM JSON output based on a text query."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("query", type=str, help="Text to search for.")
    parser.add_argument("output", type=Path, help="Path to save the filtered JSON DOM file.")

    args = parser.parse_args(argv)

    try:
        filter_dom(args.input, args.query, args.output)
        print(f"Filtered DOM saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

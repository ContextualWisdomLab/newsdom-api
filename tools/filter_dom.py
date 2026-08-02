from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def filter_dom(json_path: Path, query: str, output_path: Path | None = None) -> dict:
    """Filter DOM JSON by headline regex pattern and return the filtered DOM."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        raw_bytes = json_path.read_bytes()
        data = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern: {exc}") from exc

    pages = data.get("pages", [])
    filtered_pages = []

    for page in pages:
        articles = page.get("articles", [])

        filtered_articles = []
        for article in articles:
            headline = article.get("headline", "")
            if pattern.search(headline):
                filtered_articles.append(article)

        new_page = page.copy()
        new_page["articles"] = filtered_articles
        filtered_pages.append(new_page)

    data["pages"] = filtered_pages

    if output_path:
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return data


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter NewsDOM JSON by headline using regex."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("query", type=str, help="Regex pattern to filter headlines.")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path for the filtered JSON."
    )

    args = parser.parse_args(argv)

    try:
        filtered_data = filter_dom(args.input, args.query, args.output)
        if not args.output:
            print(json.dumps(filtered_data, ensure_ascii=False, indent=2))
        else:
            print(f"Filtered DOM saved to {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

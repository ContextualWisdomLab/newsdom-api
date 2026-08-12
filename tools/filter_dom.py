from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(json_path: Path, output_path: Path, query: str) -> None:
    """Filter DOM JSON to include only articles matching the query."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])
    filtered_pages = []

    for page in pages:
        articles = page.get("articles", [])
        filtered_articles = []
        for article in articles:
            headline = article.get("headline", "")
            body_blocks = article.get("body_blocks", [])

            # Check if query is in headline or any body block
            if query in headline or any(query in block for block in body_blocks):
                filtered_articles.append(article)

        if filtered_articles:
            # Create a copy of the page but with only the filtered articles
            new_page = dict(page)
            new_page["articles"] = filtered_articles
            filtered_pages.append(new_page)

    # Create new filtered data structure
    filtered_data = dict(data)
    filtered_data["pages"] = filtered_pages

    # Save the filtered data
    output_path.write_text(json.dumps(filtered_data, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter NewsDOM JSON to articles matching a query string."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument("query", type=str, help="Text to filter by.")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Path to save the filtered JSON.")

    args = parser.parse_args(argv)

    try:
        filter_dom(args.input, args.output, args.query)
        print("DOM filtering completed successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

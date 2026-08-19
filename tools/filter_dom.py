from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(input_path: Path, output_path: Path, keyword: str) -> None:
    """Filter articles in the DOM JSON based on a keyword in the headline."""
    if not input_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {input_path}")
    if input_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    data = json.loads(input_path.read_text(encoding="utf-8"))

    filtered_pages = []

    for page in data.get("pages", []):
        filtered_articles = []
        for article in page.get("articles", []):
            headline = article.get("headline")
            if headline and keyword.lower() in headline.lower():
                filtered_articles.append(article)

        if filtered_articles:
            # Create a copy of the page to avoid modifying the original data if referenced elsewhere
            new_page = dict(page)
            new_page["articles"] = filtered_articles
            filtered_pages.append(new_page)

    data["pages"] = filtered_pages

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON by headline keyword.")
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument("output", type=Path, help="Path to the output JSON DOM file.")
    parser.add_argument("--keyword", type=str, required=True, help="Keyword to search for in headlines.")

    args = parser.parse_args(argv)

    try:
        filter_dom(args.input, args.output, args.keyword)
        print(f"Filtering complete. Filtered DOM saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

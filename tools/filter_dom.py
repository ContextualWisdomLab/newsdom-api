from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(json_path: Path, keyword: str) -> dict:
    """Filter articles in a NewsDOM JSON file by keyword."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    # Performance optimization: Use read_bytes() and json.loads() instead of read_text()
    data = json.loads(json_path.read_bytes())

    pages = data.get("pages", [])
    filtered_pages = []

    for page in pages:
        articles = page.get("articles", [])
        filtered_articles = []
        for article in articles:
            headline = article.get("headline", "")
            body_blocks = article.get("body_blocks", [])

            # Check if keyword is in headline
            if keyword in headline:
                filtered_articles.append(article)
                continue

            # Check if keyword is in any body block
            found_in_body = False
            for block in body_blocks:
                if keyword in block:
                    found_in_body = True
                    break

            if found_in_body:
                filtered_articles.append(article)

        # Only keep pages that have at least one matched article,
        # or keep the page structure if we want to preserve page flow (we choose to keep page structure but empty articles if none match, to maintain overall DOM structure)
        # Actually, let's keep the page but only with filtered articles.
        new_page = dict(page)
        new_page["articles"] = filtered_articles
        filtered_pages.append(new_page)

    new_data = dict(data)
    new_data["pages"] = filtered_pages
    return new_data


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter articles in NewsDOM JSON by keyword."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("keyword", type=str, help="Keyword to filter articles by.")

    args = parser.parse_args(argv)

    try:
        filtered_data = filter_dom(args.input, args.keyword)
        print(json.dumps(filtered_data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

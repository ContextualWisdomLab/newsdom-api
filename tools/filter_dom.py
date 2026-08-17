from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def filter_dom(json_path: Path, output_path: Path, query: str | None = None, page_num: int | None = None) -> None:
    """Filter DOM JSON by text query or page number and save it."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")
    if output_path.suffix.lower() != ".json":
        raise ValueError("Output file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])
    filtered_pages = []

    pattern = re.compile(re.escape(query), re.IGNORECASE) if query else None

    for page in pages:
        p_num = page.get("page_number", -1)
        if page_num is not None and p_num != page_num:
            continue

        articles = page.get("articles", [])
        filtered_articles = []

        for article in articles:
            match = False
            if pattern is None:
                match = True
            else:
                headline = article.get("headline", "")
                if pattern.search(headline):
                    match = True
                else:
                    body_blocks = article.get("body_blocks", [])
                    for block in body_blocks:
                        if pattern.search(block):
                            match = True
                            break

            if match:
                filtered_articles.append(article)

        if filtered_articles or (page_num is not None and p_num == page_num and pattern is None):
            new_page = page.copy()
            new_page["articles"] = filtered_articles
            filtered_pages.append(new_page)

    data["pages"] = filtered_pages
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON output.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("output", type=Path, help="Path to save the filtered JSON.")
    parser.add_argument("-q", "--query", type=str, default=None, help="Text to search for.")
    parser.add_argument("-p", "--page", type=int, default=None, help="Page number to filter by.")

    args = parser.parse_args(argv)

    try:
        filter_dom(args.input, args.output, query=args.query, page_num=args.page)
        print(f"Filtered DOM saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

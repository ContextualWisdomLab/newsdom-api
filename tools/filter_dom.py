from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(json_path: Path, keyword: str) -> dict:
    """Filter DOM JSON by keyword in article headlines or body blocks."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    filtered_pages = []

    for page in data.get("pages", []):
        filtered_articles = []
        for article in page.get("articles", []):
            match = False
            if keyword in article.get("headline", ""):
                match = True
            if not match:
                for block in article.get("body_blocks", []):
                    if keyword in block:
                        match = True
                        break
            if match:
                filtered_articles.append(article)
        if filtered_articles:
            new_page = page.copy()
            new_page["articles"] = filtered_articles
            filtered_pages.append(new_page)

    new_data = data.copy()
    new_data["pages"] = filtered_pages
    return new_data


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON by keyword.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("keyword", type=str, help="Keyword to filter by.")
    parser.add_argument("--output", type=Path, help="Path to save the filtered JSON.")

    args = parser.parse_args(argv)

    try:
        filtered_data = filter_dom(args.input, args.keyword)
        if args.output:
            args.output.write_text(
                json.dumps(filtered_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Filtered DOM saved to {args.output}")
        else:
            print(json.dumps(filtered_data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

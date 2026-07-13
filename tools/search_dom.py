from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def search_dom(json_path: Path, query: str) -> list[dict[str, str | int]]:
    """Search for a text query in DOM JSON (headlines and body blocks)."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])
    results = []

    # Pre-compile regex for performance
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    for page in pages:
        page_num = page.get("page_number", -1)
        articles = page.get("articles", [])

        for article in articles:
            article_id = article.get("article_id", "unknown")
            headline = article.get("headline", "")

            # Search in headline
            if pattern.search(headline):
                results.append(
                    {
                        "page": page_num,
                        "article_id": article_id,
                        "type": "headline",
                        "text": headline,
                    }
                )

            # Search in body blocks
            body_blocks = article.get("body_blocks", [])
            for i, block in enumerate(body_blocks):
                if pattern.search(block):
                    results.append(
                        {
                            "page": page_num,
                            "article_id": article_id,
                            "type": "body_block",
                            "index": i,
                            "text": block,
                        }
                    )

    return results


def main(argv: list[str] | None = None) -> None:
    """Run search_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Search for text in NewsDOM JSON output."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("query", type=str, help="Text to search for.")

    args = parser.parse_args(argv)

    try:
        results = search_dom(args.input, args.query)
        if not results:
            print(f"No results found for query: '{args.query}'")
            return

        print(f"Found {len(results)} results for query: '{args.query}'")
        for res in results:
            if res["type"] == "headline":
                print(
                    f"- Page {res['page']}, Article {res['article_id']} [Headline]: {res['text']}"
                )
            elif res["type"] == "body_block":
                print(
                    f"- Page {res['page']}, Article {res['article_id']} [Body Block {res['index']}]: {res['text']}"
                )

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

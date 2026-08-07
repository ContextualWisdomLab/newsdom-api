from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(json_path: Path, keyword: str, output_path: Path) -> None:
    """Filter articles in NewsDOM JSON based on a keyword."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    if not keyword.strip():
        raise ValueError("Keyword must not be blank.")

    data = json.loads(json_path.read_text(encoding="utf-8"))

    keyword_lower = keyword.casefold()

    for page in data.get("pages", []):
        filtered_articles = []
        for article in page.get("articles", []):
            headline = article.get("headline", "")
            body_blocks = article.get("body_blocks", [])

            text_to_search = (headline + " " + " ".join(body_blocks)).casefold()
            if keyword_lower in text_to_search:
                filtered_articles.append(article)

        page["articles"] = filtered_articles

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter articles in NewsDOM JSON by keyword.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to save the filtered JSON.",
    )
    parser.add_argument(
        "-k",
        "--keyword",
        type=str,
        required=True,
        help="Keyword to filter articles.",
    )

    args = parser.parse_args(argv)

    try:
        filter_dom(args.input, args.keyword, args.output)
        print(f"Filtered JSON successfully written to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

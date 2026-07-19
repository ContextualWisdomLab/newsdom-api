from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def count_words_dom(json_path: Path) -> dict[str, int]:
    """Count total words and characters in headlines and body blocks of a NewsDOM JSON file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    # Performance optimization: Use read_bytes() and json.loads() instead of read_text()
    data = json.loads(json_path.read_bytes())

    pages = data.get("pages", [])
    total_words = 0
    total_chars = 0

    for page in pages:
        articles = page.get("articles", [])
        for article in articles:
            headline = article.get("headline", "")
            if headline:
                total_chars += len(headline)
                total_words += len(headline.split())

            body_blocks = article.get("body_blocks", [])
            for block in body_blocks:
                if block:
                    total_chars += len(block)
                    total_words += len(block.split())

    return {
        "total_words": total_words,
        "total_chars": total_chars,
    }


def main(argv: list[str] | None = None) -> None:
    """Run count_words_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Count words and characters in NewsDOM JSON."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")

    args = parser.parse_args(argv)

    try:
        stats = count_words_dom(args.input)
        print("DOM Word and Character Count Report")
        print("===================================")
        print(f"Total Words: {stats['total_words']}")
        print(f"Total Characters: {stats['total_chars']}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

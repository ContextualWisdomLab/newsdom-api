from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def analyze_dom(json_path: Path) -> dict[str, int]:
    """Analyze DOM JSON."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    data = json.loads(json_path.read_text(encoding="utf-8"))

    pages = data.get("pages", [])
    num_pages = len(pages)
    num_articles = 0
    num_images = 0
    num_body_blocks = 0

    for page in pages:
        articles = page.get("articles", [])
        num_articles += len(articles)
        for article in articles:
            num_body_blocks += len(article.get("body_blocks", []))
            num_images += len(article.get("images", []))

    return {
        "num_pages": num_pages,
        "num_articles": num_articles,
        "num_body_blocks": num_body_blocks,
        "num_images": num_images,
    }


def main(argv: list[str] | None = None) -> None:
    """Run analyze_dom main entry point."""
    parser = argparse.ArgumentParser(description="Analyze NewsDOM JSON output.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")

    args = parser.parse_args(argv)

    try:
        stats = analyze_dom(args.input)
        print("DOM Analysis Report")
        print("===================")
        print(f"Pages: {stats['num_pages']}")
        print(f"Articles: {stats['num_articles']}")
        print(f"Body Blocks: {stats['num_body_blocks']}")
        print(f"Images: {stats['num_images']}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

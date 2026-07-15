from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def compare_dom(path1: Path, path2: Path) -> dict[str, int]:
    """Compare two NewsDOM JSON files for structural differences."""
    if not path1.is_file() or not path2.is_file():
        raise FileNotFoundError("One or both input files not found.")

    data1 = json.loads(path1.read_text(encoding="utf-8"))
    data2 = json.loads(path2.read_text(encoding="utf-8"))

    def count_elements(data: dict) -> dict[str, int]:
        pages = data.get("pages", [])
        num_articles = sum(len(page.get("articles", [])) for page in pages)
        num_images = sum(
            len(article.get("images", []))
            for page in pages
            for article in page.get("articles", [])
        )
        return {
            "pages": len(pages),
            "articles": num_articles,
            "images": num_images,
        }

    counts1 = count_elements(data1)
    counts2 = count_elements(data2)

    return {
        "pages_diff": counts1["pages"] - counts2["pages"],
        "articles_diff": counts1["articles"] - counts2["articles"],
        "images_diff": counts1["images"] - counts2["images"],
    }


def main(argv: list[str] | None = None) -> None:
    """Run compare_dom main entry point."""
    parser = argparse.ArgumentParser(description="Compare two NewsDOM JSON files.")
    parser.add_argument("input1", type=Path, help="First JSON DOM file.")
    parser.add_argument("input2", type=Path, help="Second JSON DOM file.")

    args = parser.parse_args(argv)

    try:
        diffs = compare_dom(args.input1, args.input2)
        print("DOM Comparison Report")
        print("=====================")
        print(f"Pages Diff: {diffs['pages_diff']}")
        print(f"Articles Diff: {diffs['articles_diff']}")
        print(f"Images Diff: {diffs['images_diff']}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

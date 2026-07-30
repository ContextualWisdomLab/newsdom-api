from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def compare_dom(file1_path: Path, file2_path: Path) -> dict[str, dict[str, int]]:
    """Compare two DOM JSON files for structural differences."""
    for path in (file1_path, file2_path):
        if not path.is_file():
            raise FileNotFoundError(f"File not found or is not a file: {path}")
        if path.suffix.lower() != ".json":
            raise ValueError(f"Input file must be a .json file: {path}")

    data1 = json.loads(file1_path.read_text(encoding="utf-8"))
    data2 = json.loads(file2_path.read_text(encoding="utf-8"))

    stats1 = _get_stats(data1)
    stats2 = _get_stats(data2)

    return {
        "file1": stats1,
        "file2": stats2,
        "diff": {k: stats1[k] - stats2[k] for k in stats1},
    }


def _get_stats(data: dict) -> dict[str, int]:
    pages = data.get("pages", [])
    num_pages = len(pages)
    num_articles = 0
    num_blocks = 0
    num_images = 0

    for page in pages:
        articles = page.get("articles", [])
        num_articles += len(articles)
        for article in articles:
            blocks = article.get("body_blocks", [])
            num_blocks += len(blocks)
            for block in blocks:
                if block.get("type") == "image":
                    num_images += 1

    return {
        "num_pages": num_pages,
        "num_articles": num_articles,
        "num_blocks": num_blocks,
        "num_images": num_images,
    }


def main(argv: list[str] | None = None) -> None:
    """Run compare_dom main entry point."""
    parser = argparse.ArgumentParser(description="Compare two NewsDOM JSON files.")
    parser.add_argument("file1", type=Path, help="Path to the first JSON DOM file.")
    parser.add_argument("file2", type=Path, help="Path to the second JSON DOM file.")

    args = parser.parse_args(argv)

    try:
        result = compare_dom(args.file1, args.file2)
        print("DOM Comparison Report")
        print("=====================")
        for key in result["file1"]:
            f1_val = result["file1"][key]
            f2_val = result["file2"][key]
            diff = result["diff"][key]
            print(f"{key}: File1={f1_val}, File2={f2_val}, Diff={diff}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

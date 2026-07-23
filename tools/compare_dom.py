from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _count_dom_elements(data: dict) -> dict[str, int]:
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


def compare_dom(json_path1: Path, json_path2: Path) -> dict[str, dict[str, int]]:
    """Compare two DOM JSON files."""
    if not json_path1.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path1}")
    if not json_path2.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path2}")
    if json_path1.suffix.lower() != ".json" or json_path2.suffix.lower() != ".json":
        raise ValueError("Files must be .json files.")

    data1 = json.loads(json_path1.read_bytes())
    data2 = json.loads(json_path2.read_bytes())

    stats1 = _count_dom_elements(data1)
    stats2 = _count_dom_elements(data2)

    diff = {key: stats2[key] - stats1[key] for key in stats1}

    return {
        "file1": stats1,
        "file2": stats2,
        "diff": diff,
    }


def main(argv: list[str] | None = None) -> None:
    """Run compare_dom main entry point."""
    parser = argparse.ArgumentParser(description="Compare two NewsDOM JSON outputs.")
    parser.add_argument("input1", type=Path, help="Path to the first JSON DOM file.")
    parser.add_argument("input2", type=Path, help="Path to the second JSON DOM file.")

    args = parser.parse_args(argv)

    try:
        results = compare_dom(args.input1, args.input2)
        print("DOM Comparison Report")
        print("=====================")
        for key in ["num_pages", "num_articles", "num_body_blocks", "num_images"]:
            val1 = results["file1"][key]
            val2 = results["file2"][key]
            diff = results["diff"][key]
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            print(f"{key}: {val1} -> {val2} (Diff: {diff_str})")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

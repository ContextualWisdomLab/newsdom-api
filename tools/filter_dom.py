from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(json_path: Path, block_type: str, output_path: Path) -> None:
    """Filter DOM blocks by type and save to output_path."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    data = json.loads(json_path.read_text(encoding="utf-8"))

    filtered_pages = []
    for page in data.get("pages", []):
        filtered_articles = []
        for article in page.get("articles", []):
            if block_type == "all":
                filtered_blocks = article.get("body_blocks", [])
            else:
                filtered_blocks = [
                    block
                    for block in article.get("body_blocks", [])
                    if block.get("type") == block_type
                ]
            if filtered_blocks:
                article["body_blocks"] = filtered_blocks
                filtered_articles.append(article)
        if filtered_articles:
            page["articles"] = filtered_articles
            filtered_pages.append(page)

    data["pages"] = filtered_pages

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON blocks by type.")
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument(
        "output", type=Path, help="Path to save the filtered JSON DOM file."
    )
    parser.add_argument(
        "--type",
        type=str,
        required=True,
        help="Type of block to retain (e.g., text, image, text_inline_equation, etc).",
    )

    args = parser.parse_args(argv)

    try:
        filter_dom(args.input, args.type, args.output)
        print(f"Filtered DOM saved to: {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

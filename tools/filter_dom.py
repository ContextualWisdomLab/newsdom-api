from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(json_path: Path, output_path: Path, min_articles: int) -> None:
    """Filter DOM JSON pages by minimum number of articles."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input must be a .json file.")
    if output_path.suffix.lower() != ".json":
        raise ValueError("Output must be a .json file.")

    data = json.loads(json_path.read_bytes())

    pages = data.get("pages", [])
    filtered_pages = []

    for page in pages:
        articles = page.get("articles", [])
        if len(articles) >= min_articles:
            filtered_pages.append(page)

    data["pages"] = filtered_pages
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter NewsDOM JSON pages by min articles."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument("output", type=Path, help="Path to the output JSON DOM file.")
    parser.add_argument(
        "--min-articles",
        type=int,
        default=1,
        help="Minimum number of articles per page.",
    )

    args = parser.parse_args(argv)

    try:
        filter_dom(args.input, args.output, args.min_articles)
        print(f"Successfully filtered and saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

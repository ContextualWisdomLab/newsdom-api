from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(json_path: Path, min_body_blocks: int, output_path: Path | None) -> None:
    """Filter out articles that have fewer than a specific number of body blocks."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])
    filtered_pages = []

    for page in pages:
        articles = page.get("articles", [])
        filtered_articles = []
        for article in articles:
            body_blocks = article.get("body_blocks", [])
            if len(body_blocks) >= min_body_blocks:
                filtered_articles.append(article)

        if filtered_articles or not articles:
            new_page = dict(page)
            new_page["articles"] = filtered_articles
            filtered_pages.append(new_page)

    data["pages"] = filtered_pages

    filtered_json = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path is None:
        print(filtered_json)
    else:
        output_path.write_text(filtered_json, encoding="utf-8")
        print(f"Filtered DOM written to {output_path}")


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter NewsDOM JSON output by minimum body block count."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "--min-blocks",
        type=int,
        required=True,
        help="Minimum number of body blocks an article must have to be retained.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to write the filtered output. Defaults to stdout.",
    )

    args = parser.parse_args(argv)

    try:
        filter_dom(args.input, args.min_blocks, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def filter_dom(
    data: Dict[str, Any],
    exclude_ads: bool = False,
    exclude_headers: bool = False,
    exclude_footers: bool = False,
    exclude_page_numbers: bool = False,
    exclude_images: bool = False,
) -> Dict[str, Any]:
    """Filter out unwanted elements from NewsDOM JSON data in-place."""
    if "pages" not in data:
        return data

    for page in data.get("pages", []):
        if exclude_ads and "ads" in page:
            page["ads"] = []
        if exclude_headers and "headers" in page:
            page["headers"] = []
        if exclude_footers and "footers" in page:
            page["footers"] = []
        if exclude_page_numbers and "page_numbers" in page:
            page["page_numbers"] = []

        if exclude_images and "articles" in page:
            for article in page["articles"]:
                if "images" in article:
                    article["images"] = []

    return data


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter specific elements from NewsDOM JSON."
    )
    parser.add_argument("input", type=Path, help="Path to input JSON file.")
    parser.add_argument("output", type=Path, help="Path to output JSON file.")
    parser.add_argument(
        "--exclude-ads", action="store_true", help="Remove all ads blocks."
    )
    parser.add_argument(
        "--exclude-headers", action="store_true", help="Remove all header blocks."
    )
    parser.add_argument(
        "--exclude-footers", action="store_true", help="Remove all footer blocks."
    )
    parser.add_argument(
        "--exclude-page-numbers",
        action="store_true",
        help="Remove all page number blocks.",
    )
    parser.add_argument(
        "--exclude-images", action="store_true", help="Remove all image nodes."
    )

    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}", file=sys.stderr)
        sys.exit(1)

    filtered_data = filter_dom(
        data,
        exclude_ads=args.exclude_ads,
        exclude_headers=args.exclude_headers,
        exclude_footers=args.exclude_footers,
        exclude_page_numbers=args.exclude_page_numbers,
        exclude_images=args.exclude_images,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(filtered_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":  # pragma: no cover
    main()

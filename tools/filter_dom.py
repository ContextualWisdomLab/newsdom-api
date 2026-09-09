"""Filter NewsDOM JSON data based on specified criteria."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError  # noqa: E402

from newsdom_api.schemas import ParseResponse


def filter_dom(
    data: dict,
    exclude_images: bool = False,
    exclude_ads: bool = False,
    exclude_headers_footers: bool = False,
    pages_to_keep: set[int] | None = None,
) -> dict:
    """Filter the DOM data based on provided criteria."""
    try:
        response = ParseResponse.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Invalid DOM JSON: {e}") from e

    filtered_pages = []
    for page in response.pages:
        if pages_to_keep is not None and page.page_number not in pages_to_keep:
            continue

        if exclude_ads:
            page.ads = []
        if exclude_headers_footers:
            page.headers = []
            page.footers = []
            page.page_numbers = []

        for article in page.articles:
            if exclude_images:
                article.images = []
                article.captions = []

        filtered_pages.append(page)

    response.pages = filtered_pages
    return response.model_dump(mode="json")


def parse_page_ranges(pages_str: str) -> set[int]:
    """Parse a comma-separated list of pages and ranges into a set of integers."""
    pages = set()
    for part in pages_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                pages.update(range(start, end + 1))
            except ValueError:
                raise ValueError(f"Invalid page range: {part}")
        else:
            try:
                pages.add(int(part))
            except ValueError:
                raise ValueError(f"Invalid page number: {part}")
    return pages


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON output.")
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument("output", type=Path, help="Path to the output JSON DOM file.")
    parser.add_argument(
        "--exclude-images",
        action="store_true",
        help="Exclude images and their captions.",
    )
    parser.add_argument("--exclude-ads", action="store_true", help="Exclude ads.")
    parser.add_argument(
        "--exclude-headers-footers",
        action="store_true",
        help="Exclude headers, footers, and page numbers.",
    )
    parser.add_argument(
        "--pages",
        type=str,
        help="Comma-separated list of pages to keep (e.g., '1,2,4-6').",
    )

    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"Error: File not found or is not a file: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error reading JSON: {e}", file=sys.stderr)
        sys.exit(1)

    pages_to_keep = None
    if args.pages:
        try:
            pages_to_keep = parse_page_ranges(args.pages)
        except ValueError as e:
            print(f"Error parsing pages: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        filtered_data = filter_dom(
            data,
            exclude_images=args.exclude_images,
            exclude_ads=args.exclude_ads,
            exclude_headers_footers=args.exclude_headers_footers,
            pages_to_keep=pages_to_keep,
        )
    except ValueError as e:
        print(f"Error filtering DOM: {e}", file=sys.stderr)
        sys.exit(1)

    # Use atomic write pattern
    temp_output = args.output.with_suffix(".tmp")
    try:
        temp_output.write_text(
            json.dumps(filtered_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temp_output.replace(args.output)
    except Exception as e:
        if temp_output.exists():
            temp_output.unlink()  # pragma: no cover
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Successfully filtered DOM and saved to {args.output}")


if __name__ == "__main__":  # pragma: no cover
    main()

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(
    json_path: Path,
    start_page: int | None = None,
    end_page: int | None = None,
    remove_ads: bool = False,
    remove_headers: bool = False,
    remove_footers: bool = False,
    remove_page_numbers: bool = False,
) -> dict:
    """Filter DOM JSON by page range and element types."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    data = json.loads(json_path.read_bytes())
    pages = data.get("pages", [])

    filtered_pages = []

    for page in pages:
        page_num = page.get("page_number", 0)

        if start_page is not None and page_num < start_page:
            continue
        if end_page is not None and page_num > end_page:
            continue

        if remove_ads:
            page["ads"] = []
        if remove_headers:
            page["headers"] = []
        if remove_footers:
            page["footers"] = []
        if remove_page_numbers:
            page["page_numbers"] = []

        filtered_pages.append(page)

    data["pages"] = filtered_pages
    return data


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON output.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to save the filtered JSON.",
        default=None,
    )
    parser.add_argument("--start-page", type=int, help="Start page number (inclusive).")
    parser.add_argument("--end-page", type=int, help="End page number (inclusive).")
    parser.add_argument("--remove-ads", action="store_true", help="Remove all ads.")
    parser.add_argument(
        "--remove-headers", action="store_true", help="Remove all headers."
    )
    parser.add_argument(
        "--remove-footers", action="store_true", help="Remove all footers."
    )
    parser.add_argument(
        "--remove-page-numbers", action="store_true", help="Remove all page numbers."
    )

    args = parser.parse_args(argv)

    try:
        filtered_data = filter_dom(
            args.input,
            start_page=args.start_page,
            end_page=args.end_page,
            remove_ads=args.remove_ads,
            remove_headers=args.remove_headers,
            remove_footers=args.remove_footers,
            remove_page_numbers=args.remove_page_numbers,
        )

        json_output = json.dumps(filtered_data, ensure_ascii=False, indent=2)

        if args.output:
            args.output.write_text(json_output, encoding="utf-8")
            print(f"Filtered DOM saved to {args.output}")
        else:
            print(json_output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

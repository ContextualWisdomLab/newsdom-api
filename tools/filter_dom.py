from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(json_path: Path, min_page: int | None, max_page: int | None) -> dict:
    """
    Filter a NewsDOM JSON document by keeping only pages within a specified range.

    Args:
        json_path: Path to the NewsDOM JSON file to filter.
        min_page: Minimum page number to include (inclusive). If None, no lower bound is applied.
        max_page: Maximum page number to include (inclusive). If None, no upper bound is applied.

    Returns:
        dict: The filtered NewsDOM document as a Python dictionary.

    Raises:
        FileNotFoundError: If the specified file does not exist or is not a file.
        ValueError: If the file is not a JSON file, or if the page range is invalid.
    """
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    if min_page is not None and min_page < 1:
        raise ValueError("min_page must be >= 1.")
    if max_page is not None and max_page < 1:
        raise ValueError("max_page must be >= 1.")
    if min_page is not None and max_page is not None and min_page > max_page:
        raise ValueError("min_page cannot be greater than max_page.")

    data = json.loads(json_path.read_text(encoding="utf-8"))

    pages = data.get("pages", [])
    filtered_pages = []

    for page in pages:
        page_num = page.get("page_number", -1)

        if min_page is not None and page_num < min_page:
            continue
        if max_page is not None and page_num > max_page:
            continue

        filtered_pages.append(page)

    data["pages"] = filtered_pages
    return data


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter NewsDOM JSON output by page range."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "--min-page", type=int, default=None, help="Minimum page number to include."
    )
    parser.add_argument(
        "--max-page", type=int, default=None, help="Maximum page number to include."
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="Output path (default: stdout)."
    )

    args = parser.parse_args(argv)

    try:
        filtered_data = filter_dom(args.input, args.min_page, args.max_page)

        output_str = json.dumps(filtered_data, ensure_ascii=False, indent=2)

        if args.output:
            args.output.write_text(output_str, encoding="utf-8")
        else:
            print(output_str)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

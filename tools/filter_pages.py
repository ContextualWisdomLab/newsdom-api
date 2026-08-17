from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_document(json_path: Path) -> dict[str, Any]:
    """Load one NewsDOM JSON object from an existing `.json` file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("NewsDOM JSON root must be an object.")
    return data


def filter_pages(json_path: Path, start_page: int, end_page: int) -> dict[str, Any]:
    """Return a NewsDOM document containing only an inclusive page range."""
    if start_page < 1 or end_page < 1 or start_page > end_page:
        raise ValueError("Page range must use positive integers in ascending order.")

    data = _load_document(json_path)
    pages = data.get("pages", [])
    if not isinstance(pages, list):
        raise ValueError("NewsDOM pages must be a list.")

    filtered_pages: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("NewsDOM pages must contain objects.")
        page_number = page.get("page_number")
        if type(page_number) is not int or page_number < 1:
            raise ValueError("NewsDOM pages must contain positive integer page_number values.")
        if start_page <= page_number <= end_page:
            filtered_pages.append(page)

    result = dict(data)
    result["pages"] = filtered_pages
    return result


def main(argv: list[str] | None = None) -> None:
    """Run the page-filter command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Filter NewsDOM JSON output by an inclusive page range."
    )
    parser.add_argument("input", type=Path, help="Path to the NewsDOM JSON file.")
    parser.add_argument(
        "--start-page", type=int, required=True, help="Start page number (inclusive)."
    )
    parser.add_argument(
        "--end-page", type=int, required=True, help="End page number (inclusive)."
    )
    args = parser.parse_args(argv)

    try:
        filtered_data = filter_pages(args.input, args.start_page, args.end_page)
        print(json.dumps(filtered_data, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":  # pragma: no cover
    main()

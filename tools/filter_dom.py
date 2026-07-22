from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(
    json_path: Path,
    pages_to_keep: list[int] | None = None,
    remove_images: bool = False,
) -> dict:
    """Filter JSON DOM based on page numbers and remove images if requested."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    filtered_pages = []
    for page in data.get("pages", []):
        page_num = page.get("page_number")

        if pages_to_keep and page_num not in pages_to_keep:
            continue

        if remove_images:
            for article in page.get("articles", []):
                article["images"] = []

        filtered_pages.append(page)

    data["pages"] = filtered_pages
    return data


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON output.")
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument("output", type=Path, help="Path to the output JSON DOM file.")
    parser.add_argument(
        "--pages",
        type=str,
        help="Comma-separated list of page numbers to keep (e.g., 1,3,5).",
    )
    parser.add_argument(
        "--remove-images",
        action="store_true",
        help="Remove all image blocks from the DOM.",
    )

    args = parser.parse_args(argv)

    pages_to_keep = None
    if args.pages:
        try:
            pages_to_keep = [int(p.strip()) for p in args.pages.split(",")]
        except ValueError:
            print(
                "Error: --pages must be a comma-separated list of integers.",
                file=sys.stderr,
            )
            sys.exit(1)

    try:
        filtered_data = filter_dom(args.input, pages_to_keep, args.remove_images)
        args.output.write_text(
            json.dumps(filtered_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Filtered DOM saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(
    json_path: Path,
    remove_ads: bool = False,
    remove_images: bool = False,
    remove_headers: bool = False,
    remove_footers: bool = False,
) -> dict:
    """Filter specific elements from NewsDOM JSON."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    data = json.loads(json_path.read_text(encoding="utf-8"))

    for page in data.get("pages", []):
        if remove_ads and "ads" in page:
            page["ads"] = []
        if remove_headers and "headers" in page:
            page["headers"] = []
        if remove_footers and "footers" in page:
            page["footers"] = []

        if remove_images:
            for article in page.get("articles", []):
                if "images" in article:
                    article["images"] = []

    return data


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter elements from NewsDOM JSON.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to save the filtered JSON.",
        default=None,
    )
    parser.add_argument("--remove-ads", action="store_true", help="Remove ads.")
    parser.add_argument("--remove-images", action="store_true", help="Remove images.")
    parser.add_argument("--remove-headers", action="store_true", help="Remove headers.")
    parser.add_argument("--remove-footers", action="store_true", help="Remove footers.")

    args = parser.parse_args(argv)

    try:
        filtered_data = filter_dom(
            args.input,
            remove_ads=args.remove_ads,
            remove_images=args.remove_images,
            remove_headers=args.remove_headers,
            remove_footers=args.remove_footers,
        )
        output_json = json.dumps(filtered_data, ensure_ascii=False, indent=2)

        if args.output:
            args.output.write_text(output_json, encoding="utf-8")
        else:
            print(output_json)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

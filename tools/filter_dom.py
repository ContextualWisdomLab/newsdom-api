from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(
    json_path: Path,
    output_path: Path,
    remove_ads: bool = False,
    remove_headers: bool = False,
    remove_footers: bool = False,
    remove_images: bool = False,
) -> None:
    """Filter out specific sections from a NewsDOM JSON file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    for page in data.get("pages", []):
        if remove_ads and "ads" in page:
            page["ads"] = []
        if remove_headers and "headers" in page:
            page["headers"] = []
        if remove_footers and "footers" in page:
            page["footers"] = []
        if remove_images and "articles" in page:
            for article in page["articles"]:
                if "images" in article:
                    article["images"] = []

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Filter out specific sections from a NewsDOM JSON file."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "output", type=Path, help="Path to save the filtered JSON file."
    )
    parser.add_argument("--remove-ads", action="store_true", help="Remove all ads.")
    parser.add_argument(
        "--remove-headers", action="store_true", help="Remove all headers."
    )
    parser.add_argument(
        "--remove-footers", action="store_true", help="Remove all footers."
    )
    parser.add_argument(
        "--remove-images", action="store_true", help="Remove all images from articles."
    )

    args = parser.parse_args(argv)

    try:
        filter_dom(
            args.input,
            args.output,
            remove_ads=args.remove_ads,
            remove_headers=args.remove_headers,
            remove_footers=args.remove_footers,
            remove_images=args.remove_images,
        )
    except (FileNotFoundError, ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

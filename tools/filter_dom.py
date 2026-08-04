from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(
    json_path: Path,
    output_path: Path,
    *,
    remove_images: bool = False,
    remove_captions: bool = False,
    remove_ads: bool = False,
    remove_headers: bool = False,
    remove_footers: bool = False,
) -> None:
    """Filter specific elements from a NewsDOM JSON file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError(f"Input file must be a .json file: {json_path}")

    try:
        # Performance Optimization: Use path.read_bytes() directly
        data = json.loads(json_path.read_bytes())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file ({json_path}): {exc}") from exc

    for page in data.get("pages", []):
        if remove_ads:
            page["ads"] = []
        if remove_headers:
            page["headers"] = []
        if remove_footers:
            page["footers"] = []
        for article in page.get("articles", []):
            if remove_images:
                article["images"] = []
            if remove_captions:
                article["captions"] = []
                for img in article.get("images", []):
                    img["captions"] = []

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run the JSON filter CLI."""
    parser = argparse.ArgumentParser(
        description="Filter out specific elements from a NewsDOM JSON file."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to write the filtered JSON output file.",
    )
    parser.add_argument(
        "--remove-images", action="store_true", help="Remove all images."
    )
    parser.add_argument(
        "--remove-captions", action="store_true", help="Remove all captions."
    )
    parser.add_argument(
        "--remove-ads", action="store_true", help="Remove all ads."
    )
    parser.add_argument(
        "--remove-headers", action="store_true", help="Remove all headers."
    )
    parser.add_argument(
        "--remove-footers", action="store_true", help="Remove all footers."
    )

    args = parser.parse_args(argv)

    try:
        filter_dom(
            args.input,
            args.output,
            remove_images=args.remove_images,
            remove_captions=args.remove_captions,
            remove_ads=args.remove_ads,
            remove_headers=args.remove_headers,
            remove_footers=args.remove_footers,
        )
        print(f"Filtered JSON successfully written to {args.output}")
    except Exception as exc:
        print(f"Error filtering JSON file: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

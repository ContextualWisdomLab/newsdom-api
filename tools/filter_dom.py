from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from pydantic import ValidationError  # noqa: E402
from newsdom_api.schemas import ParseResponse  # noqa: E402


def filter_dom(
    json_path: Path,
    pages_to_keep: set[int] | None = None,
    no_images: bool = False,
    no_ads: bool = False,
    no_headers: bool = False,
    no_footers: bool = False,
) -> dict:
    """Filter NewsDOM JSON data according to provided criteria."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError(f"Input file must be a .json file: {json_path}")

    try:
        data = json.loads(json_path.read_bytes())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file ({json_path}): {exc}") from exc

    try:
        ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError(
            f"File {json_path} does not match ParseResponse schema: {exc}"
        ) from exc

    filtered_pages = []
    for page in data.get("pages", []):
        page_num = page.get("page_number")
        if pages_to_keep and page_num not in pages_to_keep:
            continue

        if no_ads:
            page["ads"] = []
        if no_headers:
            page["headers"] = []
        if no_footers:
            page["footers"] = []

        if no_images:
            for article in page.get("articles", []):
                article["images"] = []
                # Also remove captions and footnotes related to images if we want to be thorough,
                # but let's stick to the images array for simplicity, as they are separate nodes.

        filtered_pages.append(page)

    data["pages"] = filtered_pages
    return data


def main(argv: list[str] | None = None) -> None:
    """Run the JSON filtering CLI."""
    parser = argparse.ArgumentParser(
        description="Filter a NewsDOM JSON file (e.g. remove images, ads, or specific pages)."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-p",
        "--pages",
        type=int,
        nargs="+",
        help="Specific page numbers to keep. If not provided, all pages are kept.",
    )
    parser.add_argument(
        "--no-images", action="store_true", help="Remove all images from articles."
    )
    parser.add_argument(
        "--no-ads", action="store_true", help="Remove all ads from pages."
    )
    parser.add_argument(
        "--no-headers", action="store_true", help="Remove all headers from pages."
    )
    parser.add_argument(
        "--no-footers", action="store_true", help="Remove all footers from pages."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to output JSON file. If not provided, prints to stdout.",
    )

    args = parser.parse_args(argv)

    try:
        pages_set = set(args.pages) if args.pages else None
        filtered_data = filter_dom(
            args.input,
            pages_to_keep=pages_set,
            no_images=args.no_images,
            no_ads=args.no_ads,
            no_headers=args.no_headers,
            no_footers=args.no_footers,
        )

        out_json = json.dumps(filtered_data, ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(out_json, encoding="utf-8")
            print(f"Filtered DOM successfully written to {args.output}")
        else:
            print(out_json)
    except Exception as exc:
        print(f"Error filtering JSON file: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

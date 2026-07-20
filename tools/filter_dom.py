from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def filter_dom(
    json_path: Path,
    remove_ads: bool = False,
    remove_headers: bool = False,
    remove_footers: bool = False,
    remove_images: bool = False,
    remove_bboxes: bool = False,
) -> dict:
    """Filter out noise data from DOM JSON."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])

    for page in pages:
        if remove_ads and "ads" in page:
            page["ads"] = []
        if remove_headers and "headers" in page:
            page["headers"] = []
        if remove_footers and "footers" in page:
            page["footers"] = []

        articles = page.get("articles", [])
        for article in articles:
            if remove_images and "images" in article:
                article["images"] = []
            if remove_bboxes:
                if "bbox" in article:
                    article.pop("bbox", None)
                for image in article.get("images", []):
                    if "bbox" in image:
                        image.pop("bbox", None)
                    for cap in image.get("captions", []):
                        if "bbox" in cap:
                            cap.pop("bbox", None)
                    for fn in image.get("footnotes", []):
                        if "bbox" in fn:
                            fn.pop("bbox", None)
                for cap in article.get("captions", []):
                    if "bbox" in cap:
                        cap.pop("bbox", None)
                for fn in article.get("footnotes", []):
                    if "bbox" in fn:
                        fn.pop("bbox", None)

    return data


def main(argv: list[str] | None = None) -> None:
    """Run the filter_dom CLI."""
    parser = argparse.ArgumentParser(description="Filter noise data from NewsDOM JSON.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "-o", "--output", type=Path, help="Path to write the filtered JSON."
    )
    parser.add_argument("--remove-ads", action="store_true", help="Remove ads.")
    parser.add_argument("--remove-headers", action="store_true", help="Remove headers.")
    parser.add_argument("--remove-footers", action="store_true", help="Remove footers.")
    parser.add_argument("--remove-images", action="store_true", help="Remove images.")
    parser.add_argument(
        "--remove-bboxes", action="store_true", help="Remove bounding boxes."
    )

    args = parser.parse_args(argv)

    try:
        filtered = filter_dom(
            args.input,
            remove_ads=args.remove_ads,
            remove_headers=args.remove_headers,
            remove_footers=args.remove_footers,
            remove_images=args.remove_images,
            remove_bboxes=args.remove_bboxes,
        )
        output_json = json.dumps(filtered, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(output_json, encoding="utf-8")
        else:
            print(output_json)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

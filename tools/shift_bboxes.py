from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def _shift_bbox(bbox: Dict[str, Any], dx: float, dy: float) -> None:
    if "x0" in bbox:
        bbox["x0"] += dx
    if "x1" in bbox:
        bbox["x1"] += dx
    if "y0" in bbox:
        bbox["y0"] += dy
    if "y1" in bbox:
        bbox["y1"] += dy


def shift_bboxes(data: Dict[str, Any], dx: float, dy: float) -> Dict[str, Any]:
    """Shift all bounding boxes in NewsDOM JSON data in-place."""
    if "pages" not in data:
        return data

    for page in data.get("pages", []):
        for article in page.get("articles", []):
            if "bbox" in article and article["bbox"]:
                _shift_bbox(article["bbox"], dx, dy)
            for image in article.get("images", []):
                if "bbox" in image and image["bbox"]:
                    _shift_bbox(image["bbox"], dx, dy)
                for caption in image.get("captions", []):
                    if "bbox" in caption and caption["bbox"]:
                        _shift_bbox(caption["bbox"], dx, dy)
                for footnote in image.get("footnotes", []):
                    if "bbox" in footnote and footnote["bbox"]:
                        _shift_bbox(footnote["bbox"], dx, dy)
            for caption in article.get("captions", []):
                if "bbox" in caption and caption["bbox"]:
                    _shift_bbox(caption["bbox"], dx, dy)
            for footnote in article.get("footnotes", []):
                if "bbox" in footnote and footnote["bbox"]:
                    _shift_bbox(footnote["bbox"], dx, dy)

    return data


def main(argv: list[str] | None = None) -> None:
    """Run shift_bboxes main entry point."""
    parser = argparse.ArgumentParser(
        description="Shift all bounding boxes in NewsDOM JSON."
    )
    parser.add_argument("input", type=Path, help="Path to input JSON file.")
    parser.add_argument("output", type=Path, help="Path to output JSON file.")
    parser.add_argument(
        "--dx", type=float, default=0.0, help="Amount to shift in X direction."
    )
    parser.add_argument(
        "--dy", type=float, default=0.0, help="Amount to shift in Y direction."
    )

    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}", file=sys.stderr)
        sys.exit(1)

    shifted_data = shift_bboxes(data, dx=args.dx, dy=args.dy)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(shifted_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":  # pragma: no cover
    main()

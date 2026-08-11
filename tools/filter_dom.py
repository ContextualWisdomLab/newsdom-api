from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))  # pragma: no cover

from pydantic import ValidationError  # noqa: E402
from newsdom_api.schemas import ParseResponse  # noqa: E402

def filter_dom(json_path: Path, output_path: Path, remove_ads: bool = False, remove_images: bool = False, target_page: int | None = None) -> None:
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError(f"Input file must be a .json file: {json_path}")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file ({json_path}): {exc}") from exc

    try:
        ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"File {json_path} does not match ParseResponse schema: {exc}") from exc

    pages = data.get("pages", [])

    if target_page is not None:
        pages = [p for p in pages if p.get("page_number") == target_page]

    for page in pages:
        if remove_ads:
            page["ads"] = []
        if remove_images:
            for article in page.get("articles", []):
                article["images"] = []

    data["pages"] = pages

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Filter a NewsDOM JSON file.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Path to write the filtered JSON output file.")
    parser.add_argument("--remove-ads", action="store_true", help="Remove all ads from the pages.")
    parser.add_argument("--remove-images", action="store_true", help="Remove all images from the articles.")
    parser.add_argument("--page", type=int, help="Keep only the specified page number.", default=None)

    args = parser.parse_args(argv)

    try:
        filter_dom(args.input, args.output, remove_ads=args.remove_ads, remove_images=args.remove_images, target_page=args.page)
        print(f"Filtered JSON successfully written to {args.output}")
    except Exception as exc:
        print(f"Error filtering JSON file: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":  # pragma: no cover
    main()

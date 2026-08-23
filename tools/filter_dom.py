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

def filter_dom(json_path: Path, pages_to_keep: list[int] | None = None, remove_ads: bool = False) -> dict:
    """Filter DOM by keeping only specified pages and/or removing ads."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file ({json_path}): {exc}") from exc

    try:
        ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"File {json_path} does not match ParseResponse schema: {exc}") from exc

    filtered_pages = []

    for page in data.get("pages", []):
        page_num = page.get("page_number", 0)

        # Filter by page number
        if pages_to_keep is not None and page_num not in pages_to_keep:
            continue

        # Filter ads
        if remove_ads:
            page["ads"] = []

        filtered_pages.append(page)

    data["pages"] = filtered_pages
    return data

def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON output.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Path to the output JSON file.")
    parser.add_argument("-p", "--pages", type=int, nargs="+", help="Specific page numbers to keep.")
    parser.add_argument("--remove-ads", action="store_true", help="Remove all advertisement blocks.")

    args = parser.parse_args(argv)

    try:
        filtered_data = filter_dom(args.input, pages_to_keep=args.pages, remove_ads=args.remove_ads)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(filtered_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Filtered DOM written to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":  # pragma: no cover
    main()

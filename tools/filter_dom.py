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
    output_path: Path,
    remove_ads: bool = False,
    remove_headers: bool = False,
    remove_footers: bool = False,
) -> None:
    """Filter a NewsDOM JSON file by removing specific elements."""
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
        raise ValueError(
            f"File {json_path} does not match ParseResponse schema: {exc}"
        ) from exc

    for page in data.get("pages", []):
        if remove_ads and "ads" in page:
            page["ads"] = []
        if remove_headers and "headers" in page:
            page["headers"] = []
        if remove_footers and "footers" in page:
            page["footers"] = []

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run the JSON filter CLI."""
    parser = argparse.ArgumentParser(
        description="Filter a NewsDOM JSON file by removing specific elements."
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
        "--remove-ads", action="store_true", help="Remove all ads from the document."
    )
    parser.add_argument(
        "--remove-headers", action="store_true", help="Remove all headers from the document."
    )
    parser.add_argument(
        "--remove-footers", action="store_true", help="Remove all footers from the document."
    )

    args = parser.parse_args(argv)

    try:
        filter_dom(
            args.input,
            args.output,
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

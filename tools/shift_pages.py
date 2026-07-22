from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def shift_pages(json_path: Path, offset: int) -> dict:
    """Shift all page numbers in a JSON DOM by a given offset."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    for page in data.get("pages", []):
        current = page.get("page_number")
        if type(current) is int:
            new_num = current + offset
            page["page_number"] = max(1, new_num)

    return data


def main(argv: list[str] | None = None) -> None:
    """Run shift_pages main entry point."""
    parser = argparse.ArgumentParser(
        description="Shift page numbers in NewsDOM JSON output."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument("output", type=Path, help="Path to the output JSON DOM file.")
    parser.add_argument(
        "offset",
        type=int,
        help="Integer offset to apply to page numbers (e.g., -2, 1).",
    )

    args = parser.parse_args(argv)

    try:
        shifted_data = shift_pages(args.input, args.offset)
        args.output.write_text(
            json.dumps(shifted_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Shifted DOM saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def minify_dom(json_path: Path, output_path: Path) -> None:
    """Minify DOM JSON by removing optional formatting metadata like bbox."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    def _remove_bbox(obj: dict | list) -> None:
        if isinstance(obj, dict):
            obj.pop("bbox", None)
            for value in obj.values():
                _remove_bbox(value)
        elif isinstance(obj, list):
            for item in obj:
                _remove_bbox(item)

    _remove_bbox(data)

    output_path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    """Run minify_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Minify NewsDOM JSON by removing optional metadata and whitespace."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Path to save the minified JSON.")

    args = parser.parse_args(argv)

    try:
        minify_dom(args.input, args.output)
        print("DOM minification completed successfully.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

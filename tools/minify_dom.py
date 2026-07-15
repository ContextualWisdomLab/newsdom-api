from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def minify_dom(json_path: Path) -> str:
    """Minify NewsDOM JSON file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found: {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def main(argv: list[str] | None = None) -> None:
    """Run minify_dom main entry point."""
    parser = argparse.ArgumentParser(description="Minify NewsDOM JSON file.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("--output", type=Path, help="Path to save the minified JSON.")

    args = parser.parse_args(argv)

    try:
        minified = minify_dom(args.input)
        if args.output:
            args.output.write_text(minified, encoding="utf-8")
            print(f"Minified DOM saved to {args.output}")
        else:
            print(minified)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

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


def minify_dom(json_path: Path, output_path: Path | None = None) -> str:
    """Minify NewsDOM JSON data and optionally write it to a file."""
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

    minified_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(minified_json.encode("utf-8"))

    return minified_json


def main(argv: list[str] | None = None) -> None:
    """Run the JSON minifying CLI."""
    parser = argparse.ArgumentParser(
        description="Minify a NewsDOM JSON file, removing all extra whitespace."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to output JSON file. If not provided, prints to stdout.",
    )

    args = parser.parse_args(argv)

    try:
        minified = minify_dom(args.input, args.output)
        if args.output:
            print(f"Minified DOM successfully written to {args.output}")
        else:
            print(minified)
    except Exception as exc:
        print(f"Error minifying JSON file: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

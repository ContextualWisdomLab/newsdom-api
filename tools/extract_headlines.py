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


def extract_headlines(json_path: Path, output_path: Path) -> None:
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
    headlines = []
    for page in data.get("pages", []):
        for article in page.get("articles", []):
            headline = article.get("headline")
            if headline:
                headlines.append(headline)
    output_path.write_text("\n".join(headlines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Extract headlines from a NewsDOM JSON file."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to write the headlines text file.",
    )
    args = parser.parse_args(argv)
    try:
        extract_headlines(args.input, args.output)
        print(f"Headlines successfully written to {args.output}")
    except Exception as exc:
        print(f"Error extracting headlines: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

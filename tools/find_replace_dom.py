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


def find_replace_dom(
    json_path: Path, output_path: Path, target: str, replacement: str
) -> None:
    """Find and replace a string in a NewsDOM JSON file."""
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
        for i in range(len(page.get("ads", []))):
            page["ads"][i] = page["ads"][i].replace(target, replacement)
        for i in range(len(page.get("headers", []))):
            page["headers"][i] = page["headers"][i].replace(target, replacement)
        for i in range(len(page.get("footers", []))):
            page["footers"][i] = page["footers"][i].replace(target, replacement)
        for i in range(len(page.get("page_numbers", []))):
            page["page_numbers"][i] = page["page_numbers"][i].replace(
                target, replacement
            )

        for article in page.get("articles", []):
            article["headline"] = article["headline"].replace(target, replacement)
            for i in range(len(article.get("body_blocks", []))):
                article["body_blocks"][i] = article["body_blocks"][i].replace(
                    target, replacement
                )
            for caption in article.get("captions", []):
                caption["text"] = caption["text"].replace(target, replacement)
            for fn in article.get("footnotes", []):
                fn["text"] = fn["text"].replace(target, replacement)

            for img in article.get("images", []):
                for caption in img.get("captions", []):
                    caption["text"] = caption["text"].replace(target, replacement)
                for fn in img.get("footnotes", []):
                    fn["text"] = fn["text"].replace(target, replacement)

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run the JSON find and replace CLI."""
    parser = argparse.ArgumentParser(
        description="Find and replace text in a NewsDOM JSON file."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument("target", type=str, help="Text to find.")
    parser.add_argument("replacement", type=str, help="Text to replace with.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to write the updated JSON output file.",
    )

    args = parser.parse_args(argv)

    try:
        find_replace_dom(args.input, args.output, args.target, args.replacement)
        print(f"Updated JSON successfully written to {args.output}")
    except Exception as exc:
        print(f"Error updating JSON file: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

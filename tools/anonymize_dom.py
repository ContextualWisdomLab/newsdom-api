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


def _mask_text(text: str) -> str:
    """Mask text with asterisks of the same length."""
    return "*" * len(text)


def anonymize_dom(json_path: Path, output_path: Path) -> None:
    """Anonymize a NewsDOM JSON file by masking text content."""
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

    for page in data.get("pages", []):
        for ad in range(len(page.get("ads", []))):
            page["ads"][ad] = _mask_text(page["ads"][ad])
        for header in range(len(page.get("headers", []))):
            page["headers"][header] = _mask_text(page["headers"][header])
        for footer in range(len(page.get("footers", []))):
            page["footers"][footer] = _mask_text(page["footers"][footer])
        for article in page.get("articles", []):
            article["headline"] = _mask_text(article["headline"])
            for b in range(len(article.get("body_blocks", []))):
                article["body_blocks"][b] = _mask_text(article["body_blocks"][b])
            for caption in article.get("captions", []):
                caption["text"] = _mask_text(caption["text"])
            for fn in article.get("footnotes", []):
                fn["text"] = _mask_text(fn["text"])
            for img in article.get("images", []):
                for caption in img.get("captions", []):
                    caption["text"] = _mask_text(caption["text"])
                for fn in img.get("footnotes", []):
                    fn["text"] = _mask_text(fn["text"])

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run the JSON anonymizer CLI."""
    parser = argparse.ArgumentParser(
        description="Anonymize a NewsDOM JSON file by masking all text content."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to write the anonymized JSON output file.",
    )

    args = parser.parse_args(argv)

    try:
        anonymize_dom(args.input, args.output)
        print(f"Anonymized JSON successfully written to {args.output}")
    except Exception as exc:
        print(f"Error anonymizing JSON file: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

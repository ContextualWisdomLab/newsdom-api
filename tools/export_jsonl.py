from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from pydantic import ValidationError  # noqa: E402

from newsdom_api.schemas import ParseResponse  # noqa: E402


def _load_newsdom(json_path: Path) -> ParseResponse:
    """Load one input file and enforce the canonical NewsDOM response schema."""

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    try:
        return ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError(
            f"File {json_path} does not match ParseResponse schema: {exc}"
        ) from exc


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export canonical NewsDOM article records to an atomically published JSONL file."""

    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")
    if json_path.resolve() == output_path.resolve():
        raise ValueError("Output path must differ from input path.")

    document = _load_newsdom(json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    descriptor, staged_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
    )
    staged_path = Path(staged_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as jsonl_file:
            for page in document.pages:
                for article in page.articles:
                    record = {
                        "document_id": document.document_id,
                        "page_number": page.page_number,
                        "article_id": article.article_id,
                        "headline": article.headline,
                        "body_blocks": article.body_blocks,
                    }
                    jsonl_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            jsonl_file.flush()
            os.fsync(jsonl_file.fileno())
        staged_path.replace(output_path)
    finally:
        staged_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-JSONL export CLI."""

    parser = argparse.ArgumentParser(description="Export a NewsDOM JSON file to JSONL.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument("output", type=Path, help="Path to write the JSONL output file.")
    args = parser.parse_args(argv)

    try:
        export_jsonl(args.input, args.output)
        print(f"JSONL successfully written to {args.output}")
    except Exception as exc:
        print(f"Error exporting JSONL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

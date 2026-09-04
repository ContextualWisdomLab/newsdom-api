from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from pydantic import ValidationError

from newsdom_api.schemas import ParseResponse


def _same_file_target(source_path: Path, target_path: Path) -> bool:
    """Return whether two paths resolve to the same filesystem object.

    Resolve path aliases first, then use inode identity for an existing target so
    hard-link aliases cannot turn an export into a destructive in-place rewrite.
    """
    if source_path.resolve() == target_path.resolve():
        return True
    if not target_path.exists():
        return False
    return source_path.samefile(target_path)


def _write_jsonl_atomically(document: ParseResponse, output_path: Path) -> None:
    """Publish a complete JSONL artifact without exposing partial replacements."""
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
        text=True,
    )
    temporary_path = Path(temporary_name)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as jsonlfile:
            for page in document.pages:
                for article in page.articles:
                    article_data = {
                        "document_id": document.document_id,
                        "page_number": page.page_number,
                        **article.model_dump(mode="json"),
                    }
                    jsonlfile.write(json.dumps(article_data, ensure_ascii=False) + "\n")
            jsonlfile.flush()
            os.fsync(jsonlfile.fileno())

        os.replace(temporary_path, output_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export canonical NewsDOM sections without dropping provenance.

    The export is rejected before reading or writing when the destination aliases
    the source path, including an existing hard link to the source file. A complete
    export is staged beside the destination and atomically replaces it only after
    every record has been serialized successfully.
    """
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")
    if _same_file_target(json_path, output_path):
        raise ValueError("Output path must differ from input path.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    try:
        document = ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError("Input is not canonical NewsDOM JSON") from exc

    _write_jsonl_atomically(document, output_path)


def main(argv: list[str] | None = None) -> None:
    """Run the canonical NewsDOM JSON-to-JSONL export CLI.

    Export failures are reported on stderr and mapped to a non-zero process exit.
    """
    parser = argparse.ArgumentParser(
        description="Export canonical NewsDOM JSON sections to JSONL."
    )
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

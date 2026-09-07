from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(_SRC_ROOT))

from newsdom_api.schemas import ParseResponse  # noqa: E402


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export schema-valid NewsDOM JSON and atomically publish the JSONL file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    document = ParseResponse.model_validate(data)

    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as jsonlfile:
            temporary_path = Path(jsonlfile.name)
            for page in document.pages:
                for article in page.articles:
                    if not article.body_blocks:
                        jsonlfile.write(
                            json.dumps(
                                {
                                    "document_id": document.document_id,
                                    "page_number": page.page_number,
                                    "article_id": article.article_id,
                                    "headline": article.headline,
                                    "body_block_index": None,
                                    "body_block_text": "",
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )

                    for idx, block in enumerate(article.body_blocks):
                        jsonlfile.write(
                            json.dumps(
                                {
                                    "document_id": document.document_id,
                                    "page_number": page.page_number,
                                    "article_id": article.article_id,
                                    "headline": article.headline,
                                    "body_block_index": idx,
                                    "body_block_text": block,
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )

        temporary_path.replace(output_path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-JSONL export CLI."""
    parser = argparse.ArgumentParser(description="Export a NewsDOM JSON file to JSONL.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "output", type=Path, help="Path to write the JSONL output file."
    )

    args = parser.parse_args(argv)

    try:
        export_jsonl(args.input, args.output)
        print(f"JSONL successfully written to {args.output}")
    except Exception as exc:
        print(f"Error exporting JSONL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

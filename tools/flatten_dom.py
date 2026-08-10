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


def flatten_dom(json_path: Path) -> list[dict[str, str | int]]:
    """Flatten DOM JSON into a 1D structure for RAG pipelines."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    try:
        ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Schema validation failed: {exc}") from exc

    doc_id = data.get("document_id", "unknown")
    pages = data.get("pages", [])
    results = []

    for page in pages:
        page_num = page.get("page_number", -1)
        articles = page.get("articles", [])

        for article in articles:
            article_id = article.get("article_id", "unknown")
            headline = article.get("headline", "")
            if headline:
                results.append({
                    "document_id": doc_id,
                    "page_number": page_num,
                    "article_id": article_id,
                    "type": "headline",
                    "text": headline,
                })

            for i, block in enumerate(article.get("body_blocks", [])):
                results.append({
                    "document_id": doc_id,
                    "page_number": page_num,
                    "article_id": article_id,
                    "type": "body_block",
                    "index": i,
                    "text": block,
                })

            for caption in article.get("captions", []):
                text = caption.get("text", "")
                if text:
                    results.append({
                        "document_id": doc_id,
                        "page_number": page_num,
                        "article_id": article_id,
                        "type": "caption",
                        "text": text,
                    })

            for footnote in article.get("footnotes", []):
                text = footnote.get("text", "")
                if text:
                    results.append({
                        "document_id": doc_id,
                        "page_number": page_num,
                        "article_id": article_id,
                        "type": "footnote",
                        "text": text,
                    })

    return results


def main(argv: list[str] | None = None) -> None:
    """Run flatten_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Flatten NewsDOM JSON output into JSONL for RAG."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "--output", type=Path, help="Path to the output JSONL file.", default=None
    )

    args = parser.parse_args(argv)

    try:
        results = flatten_dom(args.input)

        if args.output:
            with args.output.open("w", encoding="utf-8") as f:
                for res in results:
                    f.write(json.dumps(res, ensure_ascii=False) + "\n")
            print(f"Flattened DOM saved to {args.output}")
        else:
            for res in results:
                print(json.dumps(res, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

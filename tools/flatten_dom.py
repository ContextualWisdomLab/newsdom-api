from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from pydantic import ValidationError  # noqa: E402
from newsdom_api.schemas import ParseResponse  # noqa: E402


def flatten_dom(json_path: Path) -> list[dict[str, Any]]:
    """Flatten DOM JSON into a 1D structure with RFC 6901 pointers for RAG pipelines."""
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
    parser = data.get("quality", {}).get("parser", "unknown")
    pages = data.get("pages", [])
    results = []

    for page_idx, page in enumerate(pages):
        page_num = page.get("page_number", -1)
        articles = page.get("articles", [])

        for art_idx, article in enumerate(articles):
            article_id = article.get("article_id", "unknown")
            base_pointer = f"#/pages/{page_idx}/articles/{art_idx}"

            headline = article.get("headline", "")
            if headline.strip():
                results.append({
                    "document_id": doc_id,
                    "page_number": page_num,
                    "article_id": article_id,
                    "parser": parser,
                    "type": "headline",
                    "text": headline,
                    "pointer": f"{base_pointer}/headline"
                })

            for i, block in enumerate(article.get("body_blocks", [])):
                if block.strip():
                    results.append({
                        "document_id": doc_id,
                        "page_number": page_num,
                        "article_id": article_id,
                        "parser": parser,
                        "type": "body_block",
                        "index": i,
                        "text": block,
                        "pointer": f"{base_pointer}/body_blocks/{i}"
                    })

            # Map images by path to link them with captions/footnotes if necessary
            images = article.get("images", [])
            for img_idx, img in enumerate(images):
                img_path = img.get("path", "")

                for cap_idx, caption in enumerate(img.get("captions", [])):
                    text = caption.get("text", "")
                    if text.strip():
                        results.append({
                            "document_id": doc_id,
                            "page_number": page_num,
                            "article_id": article_id,
                            "parser": parser,
                            "type": "image_caption",
                            "image_path": img_path,
                            "text": text,
                            "pointer": f"{base_pointer}/images/{img_idx}/captions/{cap_idx}"
                        })

                for fn_idx, footnote in enumerate(img.get("footnotes", [])):
                    text = footnote.get("text", "")
                    if text.strip():
                        results.append({
                            "document_id": doc_id,
                            "page_number": page_num,
                            "article_id": article_id,
                            "parser": parser,
                            "type": "image_footnote",
                            "image_path": img_path,
                            "text": text,
                            "pointer": f"{base_pointer}/images/{img_idx}/footnotes/{fn_idx}"
                        })

            for cap_idx, caption in enumerate(article.get("captions", [])):
                text = caption.get("text", "")
                if text.strip():
                    results.append({
                        "document_id": doc_id,
                        "page_number": page_num,
                        "article_id": article_id,
                        "parser": parser,
                        "type": "caption",
                        "text": text,
                        "pointer": f"{base_pointer}/captions/{cap_idx}"
                    })

            for fn_idx, footnote in enumerate(article.get("footnotes", [])):
                text = footnote.get("text", "")
                if text.strip():
                    results.append({
                        "document_id": doc_id,
                        "page_number": page_num,
                        "article_id": article_id,
                        "parser": parser,
                        "type": "footnote",
                        "text": text,
                        "pointer": f"{base_pointer}/footnotes/{fn_idx}"
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
            # Atomic file replacement: write to temp file then rename
            fd, temp_path = tempfile.mkstemp(
                dir=args.output.parent,
                prefix=args.output.name + ".",
                suffix=".tmp",
                text=True
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for res in results:
                    f.write(json.dumps(res, ensure_ascii=False) + "\n")
            os.replace(temp_path, args.output)
            print(f"Flattened DOM saved to {args.output}")
        else:
            for res in results:
                print(json.dumps(res, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

"""Flatten validated NewsDOM into provenance-preserving semantic JSONL records."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import TypedDict

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from pydantic import ValidationError  # noqa: E402

from newsdom_api.schemas import BoundingBox, ParseResponse  # noqa: E402


class _PageProvenance(TypedDict):
    """Typed keyword arguments shared by records from one parsed page."""

    document_id: str
    parser: str
    parse_status: str
    page_number: int
    page_width: float | None
    page_height: float | None


def _json_pointer(*tokens: str | int) -> str:
    """Return an RFC 6901 JSON Pointer for the supplied source tokens."""

    escaped_tokens = (
        str(token).replace("~", "~0").replace("/", "~1") for token in tokens
    )
    return "".join(f"/{token}" for token in escaped_tokens)


def _dump_bbox(bbox: BoundingBox | None) -> dict[str, float] | None:
    """Serialize a bounding box while preserving an explicit missing value."""

    if bbox is None:
        return None
    return bbox.model_dump()


def _append_record(
    records: list[dict[str, object]],
    *,
    document_id: str,
    parser: str,
    parse_status: str,
    page_number: int,
    page_width: float | None,
    page_height: float | None,
    article_id: str | None,
    unit_type: str,
    source_kind: str,
    source_pointer: str,
    content_index: int,
    text: str,
    article_bbox: BoundingBox | None = None,
    bbox: BoundingBox | None = None,
    image_path: str | None = None,
    image_media_type: str | None = None,
    image_bbox: BoundingBox | None = None,
) -> None:
    """Append one non-empty semantic unit with source and parser provenance."""

    if not text:
        return

    records.append(
        {
            "document_id": document_id,
            "page_number": page_number,
            "page_width": page_width,
            "page_height": page_height,
            "article_id": article_id,
            "type": unit_type,
            "source_kind": source_kind,
            "source_pointer": source_pointer,
            "record_index": len(records),
            "content_index": content_index,
            "text": text,
            "parser": parser,
            "parse_status": parse_status,
            "article_bbox": _dump_bbox(article_bbox),
            "bbox": _dump_bbox(bbox),
            "image_path": image_path,
            "image_media_type": image_media_type,
            "image_bbox": _dump_bbox(image_bbox),
        }
    )


def flatten_dom(json_path: Path) -> list[dict[str, object]]:
    """Convert a validated NewsDOM document into meaning-bearing records.

    The function emits one record for each page-level text block, article
    headline, body block, caption, footnote, and image-linked caption or
    footnote. Each record retains a JSON Pointer to the exact source value,
    parser provenance, page geometry, and relevant article or image metadata.
    Empty source fields are omitted rather than converted into artificial
    embedding chunks.

    Args:
        json_path: Path to a JSON file that satisfies ``ParseResponse``.

    Returns:
        Ordered records suitable for JSONL ingestion by retrieval pipelines.

    Raises:
        FileNotFoundError: If ``json_path`` is missing or is not a file.
        ValueError: If the extension, JSON syntax, or schema is invalid.
        OSError: If the input cannot be read.
    """

    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError(f"Input file must be a .json file: {json_path}")

    try:
        raw_data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file ({json_path}): {exc}") from exc

    try:
        document = ParseResponse.model_validate(raw_data)
    except ValidationError as exc:
        raise ValueError(
            f"File {json_path} does not match ParseResponse schema: {exc}"
        ) from exc

    records: list[dict[str, object]] = []
    parser = document.quality.parser
    parse_status = document.quality.status

    for page_index, page in enumerate(document.pages):
        common_page: _PageProvenance = {
            "document_id": document.document_id,
            "parser": parser,
            "parse_status": parse_status,
            "page_number": page.page_number,
            "page_width": page.width,
            "page_height": page.height,
        }

        for content_index, text in enumerate(page.headers):
            _append_record(
                records,
                **common_page,
                article_id=None,
                unit_type="page_header",
                source_kind="text",
                source_pointer=_json_pointer(
                    "pages", page_index, "headers", content_index
                ),
                content_index=content_index,
                text=text,
            )

        for content_index, text in enumerate(page.page_numbers):
            _append_record(
                records,
                **common_page,
                article_id=None,
                unit_type="page_number",
                source_kind="text",
                source_pointer=_json_pointer(
                    "pages", page_index, "page_numbers", content_index
                ),
                content_index=content_index,
                text=text,
            )

        for article_index, article in enumerate(page.articles):
            article_pointer = (
                "pages",
                page_index,
                "articles",
                article_index,
            )
            _append_record(
                records,
                **common_page,
                article_id=article.article_id,
                unit_type="headline",
                source_kind="text",
                source_pointer=_json_pointer(*article_pointer, "headline"),
                content_index=0,
                text=article.headline,
                article_bbox=article.bbox,
            )

            for content_index, text in enumerate(article.body_blocks):
                _append_record(
                    records,
                    **common_page,
                    article_id=article.article_id,
                    unit_type="body_block",
                    source_kind="text",
                    source_pointer=_json_pointer(
                        *article_pointer, "body_blocks", content_index
                    ),
                    content_index=content_index,
                    text=text,
                    article_bbox=article.bbox,
                )

            for image_index, image in enumerate(article.images):
                image_pointer = (*article_pointer, "images", image_index)
                for content_index, caption in enumerate(image.captions):
                    _append_record(
                        records,
                        **common_page,
                        article_id=article.article_id,
                        unit_type="image_caption",
                        source_kind="image_text",
                        source_pointer=_json_pointer(
                            *image_pointer, "captions", content_index, "text"
                        ),
                        content_index=content_index,
                        text=caption.text,
                        article_bbox=article.bbox,
                        bbox=caption.bbox,
                        image_path=image.path,
                        image_media_type=image.media_type,
                        image_bbox=image.bbox,
                    )

                for content_index, footnote in enumerate(image.footnotes):
                    _append_record(
                        records,
                        **common_page,
                        article_id=article.article_id,
                        unit_type="image_footnote",
                        source_kind="image_text",
                        source_pointer=_json_pointer(
                            *image_pointer, "footnotes", content_index, "text"
                        ),
                        content_index=content_index,
                        text=footnote.text,
                        article_bbox=article.bbox,
                        bbox=footnote.bbox,
                        image_path=image.path,
                        image_media_type=image.media_type,
                        image_bbox=image.bbox,
                    )

            for content_index, caption in enumerate(article.captions):
                _append_record(
                    records,
                    **common_page,
                    article_id=article.article_id,
                    unit_type="caption",
                    source_kind="text",
                    source_pointer=_json_pointer(
                        *article_pointer, "captions", content_index, "text"
                    ),
                    content_index=content_index,
                    text=caption.text,
                    article_bbox=article.bbox,
                    bbox=caption.bbox,
                )

            for content_index, footnote in enumerate(article.footnotes):
                _append_record(
                    records,
                    **common_page,
                    article_id=article.article_id,
                    unit_type="footnote",
                    source_kind="text",
                    source_pointer=_json_pointer(
                        *article_pointer, "footnotes", content_index, "text"
                    ),
                    content_index=content_index,
                    text=footnote.text,
                    article_bbox=article.bbox,
                    bbox=footnote.bbox,
                )

        for content_index, text in enumerate(page.ads):
            _append_record(
                records,
                **common_page,
                article_id=None,
                unit_type="advertisement",
                source_kind="text",
                source_pointer=_json_pointer(
                    "pages", page_index, "ads", content_index
                ),
                content_index=content_index,
                text=text,
            )

        for content_index, text in enumerate(page.footers):
            _append_record(
                records,
                **common_page,
                article_id=None,
                unit_type="page_footer",
                source_kind="text",
                source_pointer=_json_pointer(
                    "pages", page_index, "footers", content_index
                ),
                content_index=content_index,
                text=text,
            )

    return records


def _write_jsonl_atomically(
    output_path: Path, records: list[dict[str, object]]
) -> None:
    """Write complete JSONL to a sibling temporary file before replacement."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary_path = Path(temporary_file.name)

    try:
        with temporary_file:
            for record in records:
                temporary_file.write(
                    json.dumps(record, ensure_ascii=False, separators=(",", ":"))
                    + "\n"
                )
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> None:
    """Run the provenance-preserving NewsDOM-to-JSONL command-line tool."""

    parser = argparse.ArgumentParser(
        description=(
            "Flatten validated NewsDOM JSON into provenance-preserving semantic "
            "JSONL records for retrieval pipelines."
        )
    )
    parser.add_argument("input", type=Path, help="Path to the input NewsDOM JSON.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional JSONL output path; stdout is used when omitted.",
    )
    args = parser.parse_args(argv)

    try:
        records = flatten_dom(args.input)
        if args.output is not None:
            _write_jsonl_atomically(args.output, records)
            print(f"Flattened DOM saved to {args.output}")
        else:
            for record in records:
                print(
                    json.dumps(
                        record, ensure_ascii=False, separators=(",", ":")
                    )
                )
    except (OSError, ValueError) as exc:
        print(f"Error flattening JSON file: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

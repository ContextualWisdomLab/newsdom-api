from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def _check_depth(
    obj: dict | list | str | int | float | bool | None, current_depth: int = 0
) -> None:
    if current_depth > 100:
        raise ValueError("JSON nesting depth exceeds 100.")
    if isinstance(obj, dict):
        for v in obj.values():
            _check_depth(v, current_depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            _check_depth(v, current_depth + 1)


def filter_dom(
    json_path: Path,
    remove_ads: bool = False,
    remove_headers: bool = False,
    remove_footers: bool = False,
    remove_images: bool = False,
    remove_bboxes: bool = False,
) -> dict:
    """Filter out noise data from DOM JSON."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    fd = os.open(str(json_path), os.O_RDONLY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if st.st_size > 32 * 1024 * 1024:
            raise ValueError("Input file exceeds 32 MiB limit.")
        raw_bytes = os.read(fd, st.st_size + 1)
        if len(raw_bytes) > 32 * 1024 * 1024:
            raise ValueError("Input file exceeds 32 MiB limit.")
    finally:
        os.close(fd)

    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    _check_depth(data)

    pages = data.get("pages", [])
    if not isinstance(pages, list):
        return data

    for page in pages:
        if not isinstance(page, dict):
            continue
        if remove_ads and "ads" in page:
            page["ads"] = []
        if remove_headers and "headers" in page:
            page["headers"] = []
        if remove_footers and "footers" in page:
            page["footers"] = []

        articles = page.get("articles", [])
        if not isinstance(articles, list):
            continue
        for article in articles:
            if not isinstance(article, dict):
                continue
            if remove_images and "images" in article:
                article["images"] = []
            if remove_bboxes:
                if "bbox" in article:
                    article.pop("bbox", None)
                images = article.get("images", [])
                if isinstance(images, list):
                    for image in images:
                        if not isinstance(image, dict):
                            continue
                        if "bbox" in image:
                            image.pop("bbox", None)
                        captions = image.get("captions", [])
                        if isinstance(captions, list):
                            for cap in captions:
                                if isinstance(cap, dict) and "bbox" in cap:
                                    cap.pop("bbox", None)
                        footnotes = image.get("footnotes", [])
                        if isinstance(footnotes, list):
                            for fn in footnotes:
                                if isinstance(fn, dict) and "bbox" in fn:
                                    fn.pop("bbox", None)
                captions = article.get("captions", [])
                if isinstance(captions, list):
                    for cap in captions:
                        if isinstance(cap, dict) and "bbox" in cap:
                            cap.pop("bbox", None)
                footnotes = article.get("footnotes", [])
                if isinstance(footnotes, list):
                    for fn in footnotes:
                        if isinstance(fn, dict) and "bbox" in fn:
                            fn.pop("bbox", None)

    return data


def main(argv: list[str] | None = None) -> None:
    """Run the filter_dom CLI."""
    parser = argparse.ArgumentParser(description="Filter noise data from NewsDOM JSON.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "-o", "--output", type=Path, help="Path to write the filtered JSON."
    )
    parser.add_argument("--remove-ads", action="store_true", help="Remove ads.")
    parser.add_argument("--remove-headers", action="store_true", help="Remove headers.")
    parser.add_argument("--remove-footers", action="store_true", help="Remove footers.")
    parser.add_argument("--remove-images", action="store_true", help="Remove images.")
    parser.add_argument(
        "--remove-bboxes", action="store_true", help="Remove bounding boxes."
    )

    args = parser.parse_args(argv)

    try:
        filtered = filter_dom(
            args.input,
            remove_ads=args.remove_ads,
            remove_headers=args.remove_headers,
            remove_footers=args.remove_footers,
            remove_images=args.remove_images,
            remove_bboxes=args.remove_bboxes,
        )

        output_json = json.dumps(filtered, ensure_ascii=False)
        output_bytes = output_json.encode("utf-8")

        if len(output_bytes) > 64 * 1024 * 1024:
            raise ValueError("Output size exceeds 64 MiB limit.")

        if args.output:
            out_path = args.output.resolve()
            cwd = Path.cwd().resolve()
            if not str(out_path).startswith(str(cwd)):
                raise ValueError(
                    "Output path must be within the current working directory."
                )

            fd, temp_path_str = tempfile.mkstemp(dir=str(out_path.parent))
            temp_path = Path(temp_path_str)
            try:
                os.write(fd, output_bytes)
                os.fsync(fd)
                os.close(fd)
                os.replace(temp_path, out_path)
            except Exception:
                if temp_path.exists():
                    temp_path.unlink()
                raise
        else:
            sys.stdout.write(output_json + "\n")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def extract_images(json_path: Path) -> list[dict]:
    """Extract images from NewsDOM JSON."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    pages = data.get("pages", [])

    extracted_images = []

    for page in pages:
        page_num = page.get("page_number", None)
        for article in page.get("articles", []):
            for image in article.get("images", []):
                img_data = {
                    "page_number": page_num,
                    "path": image.get("path", "")
                }

                captions = image.get("captions", [])
                if captions:
                    caption_texts = []
                    for caption in captions:
                        if isinstance(caption, dict) and "text" in caption:
                            caption_texts.append(caption["text"])
                        else:
                            caption_texts.append(str(caption))
                    img_data["captions"] = caption_texts

                extracted_images.append(img_data)

    return extracted_images


def main(argv: list[str] | None = None) -> None:
    """Run extract_images main entry point."""
    parser = argparse.ArgumentParser(description="Extract image info from NewsDOM JSON.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to save the extracted images info as JSON.",
        default=None,
    )

    args = parser.parse_args(argv)

    try:
        images_info = extract_images(args.input)
        if args.output:
            args.output.write_text(json.dumps(images_info, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            print(json.dumps(images_info, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
